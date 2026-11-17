# Docker twin of analysis.def: the environment for your own downstream code,
# built from the locked conda environment. Use it when you want GitHub to build
# the image for you instead of running `apptainer build` yourself.
#
# Needs containers/environment.lock.yml (see containers/README.md).
# .github/workflows/container.yml builds it and publishes it to
# ghcr.io/<owner>/<repo>. On TSCC:
#   singularity pull analysis.sif docker://ghcr.io/<owner>/<repo>:latest
#   singularity exec analysis.sif python my_analysis.py
# Pin the base image by digest for a final analysis (docker buildx imagetools inspect).
FROM mambaorg/micromamba:2.0.5

COPY --chown=$MAMBA_USER:$MAMBA_USER containers/environment.lock.yml /tmp/env.yml
RUN micromamba install -y -n base -f /tmp/env.yml && micromamba clean -a -y

# Singularity does not run micromamba's activation entrypoint, so put the
# environment on PATH directly.
ENV PATH=/opt/conda/bin:$PATH
