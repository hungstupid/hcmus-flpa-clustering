/* Standalone timing wrapper for the original igraph binary. */
#define _POSIX_C_SOURCE 200809L
#include <igraph.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double seconds(void) {
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    return (double) now.tv_sec + (double) now.tv_nsec / 1e9;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--commit") == 0) {
        const char *version;
        igraph_version(&version, NULL, NULL, NULL);
        if (strcmp(version, "0.9.6-48-gb89649877") != 0) {
            fprintf(stderr, "Unexpected igraph version %s\n", version);
            return EXIT_FAILURE;
        }
        puts("b89649877e15a2a4d3ca199c9190fe3dc181c643");
        return EXIT_SUCCESS;
    }
    if (argc != 3) {
        return EXIT_FAILURE;
    }
    igraph_lpa_variant_t variant;
    if (strcmp(argv[1], "lpa") == 0) {
        variant = IGRAPH_LPA_DOMINANCE;
    } else if (strcmp(argv[1], "retention_lpa") == 0) {
        variant = IGRAPH_LPA_RETENTION;
    } else if (strcmp(argv[1], "flpa") == 0) {
        variant = IGRAPH_LPA_FAST;
    } else {
        return EXIT_FAILURE;
    }

    long n, m;
    if (scanf("%ld %ld", &n, &m) != 2 || n < 0 || m < 0) {
        return EXIT_FAILURE;
    }
    igraph_vector_t edges, labels;
    igraph_vector_init(&edges, 2 * m);
    igraph_vector_init(&labels, 0);
    for (long index = 0; index < 2 * m; ++index) {
        long node;
        if (scanf("%ld", &node) != 1 || node < 0 || node >= n) {
            igraph_vector_destroy(&labels);
            igraph_vector_destroy(&edges);
            return EXIT_FAILURE;
        }
        VECTOR(edges)[index] = node;
    }

    igraph_t graph;
    igraph_create(&graph, &edges, n, IGRAPH_UNDIRECTED);
    igraph_rng_seed(igraph_rng_default(), strtoul(argv[2], NULL, 10));
    double start = seconds();
    int status = igraph_community_label_propagation(&graph, &labels, NULL, NULL, NULL, NULL, variant);
    double elapsed = seconds() - start;
    if (status == IGRAPH_SUCCESS) {
        printf("%.12g\n", elapsed);
        for (long index = 0; index < n; ++index) {
            printf("%s%ld", index ? " " : "", (long) VECTOR(labels)[index]);
        }
        putchar('\n');
    }
    igraph_destroy(&graph);
    igraph_vector_destroy(&labels);
    igraph_vector_destroy(&edges);
    return status == IGRAPH_SUCCESS ? EXIT_SUCCESS : EXIT_FAILURE;
}
