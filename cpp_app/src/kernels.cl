// Reliability calculation + Filter 1
// Author: IFF-3-2 Aleksandravicius Linas

#define ITERATIONS 4000000
#define THRESHOLD 50.0f

__kernel void compute_reliability(
    __global const int* uptimes,
    __global const float* loads,
    __global const int* ids,
    __global float* out_reliability,
    __global int* out_ids,
    __global int* counter,
    const int count
) {
    int gid = get_global_id(0);
    int gsize = get_global_size(0);

    for (int idx = gid; idx < count; idx += gsize) {
        float reliability = 0.5f;
        int uptime = uptimes[idx];
        float load = loads[idx];

        for (int i = 0; i < ITERATIONS; i++) {
            float f1 = sin((float)uptime / 1000.0f * (float)i);
            float f2 = cos(load * (float)i);
            reliability = fabs(sin(reliability + f1 - f2));
        }
        reliability *= 100.0f;

        if (reliability >= THRESHOLD) {
            int out_idx = atomic_inc(counter);
            out_reliability[out_idx] = reliability;
            out_ids[out_idx] = ids[idx];
        }
    }
}
