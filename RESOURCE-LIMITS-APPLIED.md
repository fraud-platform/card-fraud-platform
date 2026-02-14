# Resource Limits Applied - 2026-02-09

## Summary of Changes

All containers now have proper CPU and memory limits to prevent unbounded host resource usage.

### Infrastructure Containers (docker-compose.yml)

| Container | Memory | CPU Limit | CPU Reserved | Changes |
|-----------|--------|-----------|--------------|---------|
| **Redis** | **512MB** | **2 cores** | **1 core** | ✅ Increased from 256MB, added CPU limits |
| **Redpanda** | **2GB** | **1 core** | **1 core** | ✅ Increased from 1GB, added Docker limits |
| **PostgreSQL** | **512MB** | **1 core** | **0.5 cores** | ✅ Added limits (was unbounded) |
| **MinIO** | **512MB** | **1 core** | **0.5 cores** | ✅ Added limits (was unbounded) |

### Application Containers (docker-compose.apps.yml)

| Container | Memory | CPU Limit | CPU Reserved | JVM Heap | Changes |
|-----------|--------|-----------|--------------|----------|---------|
| **Rule Engine** | **2GB** | **4 cores** | **2 cores** | **1.5GB** | ✅ Added CPU limits + JVM heap config |

---

## Total Resource Allocation

**Memory:** 5.5GB total
- Rule Engine: 2GB
- Redpanda: 2GB
- Redis: 512MB
- PostgreSQL: 512MB
- MinIO: 512MB

**CPU:** 9 cores (limit), 5 cores (reserved)
- Rule Engine: 4 cores (limit), 2 cores (reserved)
- Redis: 2 cores (limit), 1 core (reserved)
- Redpanda: 1 core (both)
- PostgreSQL: 1 core (limit), 0.5 cores (reserved)
- MinIO: 1 core (limit), 0.5 cores (reserved)

**Host Requirements:**
- Minimum: 8GB RAM, 8 cores
- Recommended: 16GB RAM, 12 cores
- Plus headroom for OS and Docker overhead

---

## Key Improvements

### 1. Rule Engine - JVM Now Knows Container Limits ✅

**Before:**
```yaml
deploy:
  resources:
    limits:
      memory: 2G      # Docker knew
environment:
  # NO -Xmx!           # JVM didn't know (used host RAM)
```

**After:**
```yaml
deploy:
  resources:
    limits:
      cpus: '4'       # NEW: Prevents starving other containers
      memory: 2G
    reservations:
      cpus: '2'       # NEW: Guarantees baseline performance
      memory: 1G
environment:
  - JAVA_OPTS=-Xms1G -Xmx1536M -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+AlwaysPreTouch
  #              ^^^^^^^^^^^^^ NEW: JVM knows container limit!
```

**Why 1536M (1.5GB) heap for 2GB container:**
- JVM heap: 1.5GB (75%)
- Non-heap (MetaSpace, threads, native buffers): 512MB (25%)
- Safe headroom to avoid OOM kills

---

### 2. Redis - Doubled Memory + CPU Limits ✅

**Before:**
```bash
command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
# No CPU limits - could use all host CPU
```

**After:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2'       # NEW: Redis + I/O threads
      memory: 512M    # NEW: Docker enforces
command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
#                                  ^^^^^ DOUBLED
```

**Why 512MB:**
- 256MB was OK but tight for Redis Streams outbox
- 512MB gives headroom for 100-200 concurrent users
- Prevents evictions during load spikes

**Why 2 CPU cores:**
- Redis is single-threaded for commands
- But uses extra threads for AOF persistence + network I/O
- 2 cores prevent I/O bottlenecks

---

### 3. PostgreSQL & MinIO - Added Limits to Prevent Interference ✅

**Before:**
```yaml
# NO resource limits - could steal all host resources
```

**After:**
```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

**Why add limits:**
- Load tests don't heavily use these services
- Limits prevent accidental resource stealing
- Keeps them healthy without over-provisioning

---

## Expected Performance Impact

### Hypothesis

**Adding resource limits should IMPROVE performance by ~30%:**

| Metric | Before (Unlimited Resources) | Expected After | Improvement |
|--------|------------------------------|----------------|-------------|
| **P50** | 110ms | **~100ms** | ~10% faster |
| **P95** | 320ms | **~220ms** | **~30% faster** |
| **P99** | 870ms | **~600ms** | ~30% faster |

**Why improvement:**
1. **Less CPU contention** - Each container has guaranteed CPU allocation
2. **More predictable scheduling** - OS scheduler can optimize with known limits
3. **No JVM OOM risk** - Heap sized correctly for container
4. **No Redis evictions** - 512MB headroom prevents data loss

**Most improvement at high percentiles (P95+):**
- P50 (median) already good (streaming parser helped)
- P95/P99 were suffering from resource contention
- Limits eliminate contention → more consistent performance

---

## Files Modified

1. ✅ `docker-compose.yml` - Infrastructure containers
   - Redis: 256MB → 512MB, added CPU limits (2 cores)
   - Redpanda: 1GB → 2GB, added Docker limits (1 core)
   - PostgreSQL: Added 512MB memory + 1 core CPU limit
   - MinIO: Added 512MB memory + 1 core CPU limit

2. ✅ `docker-compose.apps.yml` - Application containers
   - Rule Engine: Added 4-core CPU limit, 2-core reservation, JVM heap config

---

## Rebuild and Restart Instructions

### Option A: Full Rebuild (Recommended for Clean Start)

```bash
cd /c/Users/kanna/github/card-fraud-platform

# 1. Stop all containers
doppler run -- docker compose -f docker-compose.yml -f docker-compose.apps.yml --profile apps down

# 2. Rebuild rule-engine (picks up new JAVA_OPTS)
doppler run -- docker compose -f docker-compose.yml -f docker-compose.apps.yml build rule-engine

# 3. Start infra + apps
doppler run -- docker compose -f docker-compose.yml -f docker-compose.apps.yml --profile apps up -d

# 4. Wait for all services to be healthy (~30 seconds)
watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}"'
# Press Ctrl+C when all show "healthy"
```

### Option B: Quick Restart (If No Code Changes)

```bash
cd /c/Users/kanna/github/card-fraud-platform

# Just restart (Docker applies new resource limits)
doppler run -- docker compose -f docker-compose.yml -f docker-compose.apps.yml --profile apps restart
```

**Note:** Option A is recommended because:
- Ensures JAVA_OPTS environment variable is picked up
- Clean state for testing
- Verifies all containers start successfully with new limits

---

## Verification Commands

### Check Resource Limits Applied

```bash
# Rule Engine
docker inspect card-fraud-rule-engine-auth | grep -A 10 "\"Resources\""

# Redis
docker inspect card-fraud-redis | grep -A 10 "\"Resources\""

# All containers
for container in card-fraud-rule-engine-auth card-fraud-redis card-fraud-postgres card-fraud-minio card-fraud-redpanda; do
  echo "=== $container ==="
  docker inspect $container | jq '.[0].HostConfig.Resources | {Memory, NanoCpus, CpuShares}'
done
```

**Expected output format:**
```json
{
  "Memory": 2147483648,        // 2GB in bytes
  "NanoCpus": 4000000000,      // 4 cores in nanoseconds
  "CpuShares": 0
}
```

### Monitor Resource Usage During Load Test

```bash
# Real-time stats (updates every 2 seconds)
docker stats

# Snapshot
docker stats --no-stream

# Specific containers only
docker stats card-fraud-rule-engine-auth card-fraud-redis
```

**Watch for:**
- Memory: Should stay under limits (e.g., Rule Engine < 2GB)
- CPU: Should use available allocation efficiently
- No OOM kills or restarts

### Check JVM Heap Configuration

```bash
# Exec into running container
docker exec -it card-fraud-rule-engine-auth sh

# Check JVM flags
ps aux | grep java

# Should see: -Xms1G -Xmx1536M
```

---

## Load Test with New Resource Limits

### Run Baseline Test

```bash
cd /c/Users/kanna/github/card-fraud-e2e-load-testing

# Start fresh load test
uv run lt-run \
  --service rule-engine \
  --users=100 \
  --spawn-rate=20 \
  --run-time=2m \
  --scenario baseline \
  --auth-mode none \
  --headless
```

### In Another Terminal: Monitor Resources

```bash
# Terminal 1: Watch Docker stats
docker stats

# Terminal 2: Watch container logs
docker logs -f card-fraud-rule-engine-auth
```

### Compare Results

**Before (unlimited resources):**
- P50: 110ms
- P95: 320ms
- P99: 870ms

**Expected after (with limits):**
- P50: ~100ms (minor improvement)
- P95: ~220ms (30% improvement)
- P99: ~600ms (30% improvement)

---

## Troubleshooting

### If Container Fails to Start

**Check logs:**
```bash
docker logs card-fraud-rule-engine-auth
```

**Common issues:**
1. **OOM Killed** - JVM trying to use > 2GB
   - Fix: Verify JAVA_OPTS is applied (`docker inspect` → Env)
   - Should see: `-Xmx1536M`

2. **CPU Starvation** - Not enough CPU for startup
   - Increase CPU reservation temporarily
   - Or reduce concurrent service startup

3. **Memory Limit Too Low** - PostgreSQL/MinIO can't start
   - Check if 512MB is sufficient
   - May need to increase for cold start

### If Performance is Worse

**Possible causes:**
1. **CPU limits too strict** - Containers can't scale with load
   - Monitor `docker stats` - if CPU at 100%, increase limit
2. **Memory too tight** - Swapping or evictions
   - Check Redis evictions: `docker exec card-fraud-redis redis-cli info stats | grep evicted`
3. **Thread contention** - Worker pools mismatched to CPU allocation
   - May need to adjust pool sizes in application.yaml

---

## Next Steps After Restart

1. ✅ **Verify all containers healthy**
   ```bash
   docker ps
   # All should show "healthy" status
   ```

2. ✅ **Run baseline load test**
   - Compare P50/P95/P99 to previous results
   - Monitor `docker stats` during test

3. ✅ **Analyze JFR recording**
   - Extract from container: `docker cp card-fraud-rule-engine-auth:/tmp/flight.jfr ./flight-with-limits.jfr`
   - Compare CPU usage before/after limits

4. ✅ **Tune pool sizes** (if needed)
   - If P95 still high: Test Redis pool 30 → 50
   - If CPU < 80%: May have headroom to increase

---

**Resource limits applied:** 2026-02-09
**Ready for load testing with proper infrastructure configuration!**

