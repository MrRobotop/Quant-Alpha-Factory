# Real Qlib And RD-Agent Execution

This repository is designed so CI and demos run without external services, but real Qlib and
RD-Agent execution are supported when the user provides the required local environment.

## Recommended Environment

Use Linux or WSL2 for real execution.

Recommended Python:

- Qlib: Python 3.8 through 3.12 are supported by the current Qlib project guidance.
- RD-Agent: Python 3.10 or 3.11 are well tested in RD-Agent CI.
- Practical choice for this repository: Python 3.11.

RD-Agent currently documents Linux support and recommends Docker for isolated code execution. Before
running RD-Agent workflows, verify:

```bash
docker run hello-world
```

## Install Project With Real Extras

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,api,dashboard,qlib,rdagent]"
```

The repository also exposes the same install path as:

```bash
make install-real
```

On macOS, Qlib/LightGBM may require OpenMP:

```bash
brew install libomp
```

## Configure Credentials

Copy the example environment file:

```bash
cp .env.example .env
```

For OpenAI-compatible LiteLLM usage:

```bash
OPENAI_API_KEY=<your_api_key>
OPENAI_API_BASE=<optional_base_url>
CHAT_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
DS_CODER_COSTEER_ENV_TYPE=docker
```

For Azure OpenAI:

```bash
AZURE_API_KEY=<your_key>
AZURE_API_BASE=<your_endpoint>
AZURE_API_VERSION=<api_version>
CHAT_MODEL=azure/<chat_deployment_name>
EMBEDDING_MODEL=azure/<embedding_deployment_name>
DS_CODER_COSTEER_ENV_TYPE=docker
```

Then load the environment:

```bash
export $(grep -v '^#' .env | xargs)
```

Do not commit `.env`.

## Preflight Check

Run the project doctor before real execution:

```bash
python -m src.cli doctor --component all
```

Use strict mode in automation or before a real run:

```bash
python -m src.cli doctor --component qlib --strict
python -m src.cli doctor --component rdagent --strict
```

For public repository users who have not configured LLM credentials yet, validate the non-secret
RD-Agent prerequisites with:

```bash
DS_CODER_COSTEER_ENV_TYPE=docker \
  python -m src.cli doctor --component rdagent --allow-missing-llm --strict
```

This checks Python, RD-Agent installation, Docker, and Docker daemon reachability while reporting
missing LLM credentials as a warning. Real RD-Agent workflows still require provider credentials.

The doctor checks Python compatibility, Qlib importability, `qrun`, RD-Agent, Docker, Docker daemon
reachability, configured LLM credential variables, and the Qlib `provider_uri`. It prints only
whether credential variables are present; it does not print secret values.

## Real Qlib Path

1. Run Qlib preflight:

```bash
python -m src.cli doctor --component qlib --strict
```

2. Validate input data:

```bash
python -m src.cli data validate --input data/sample/prices.csv
```

3. Convert data to Qlib storage. For production usage, point `--input` to validated user-provided
   market data and `--output` to a persistent Qlib provider directory:

```bash
python -m src.cli data convert \
  --input data/sample/prices.csv \
  --output data/qlib_bin/sample \
  --execute
```

4. Confirm the Qlib config points to the provider directory:

```yaml
qlib_init:
  provider_uri: data/qlib_bin/sample
```

5. Run research checks:

```bash
python -m src.cli research check \
  --config configs/qlib/baseline_lightgbm_alpha158.yaml
```

6. Execute Qlib:

```bash
python -m src.cli qlib run \
  --config configs/qlib/baseline_lightgbm_alpha158.yaml \
  --execute
```

Alternatively, run the project-level synthetic Qlib demo:

```bash
python -m src.cli qlib demo --execute
```

This wraps validation, conversion, research checks, qrun execution, Qlib/MLflow metric parsing, and
project manifest creation.

The equivalent Make target is:

```bash
make qlib-demo-real
```

Real Qlib outputs should be parsed and recorded into experiment manifests before being reported.
Do not publish or compare metrics until the manifest, logs, config, data version, costs, and
artifact paths are present in stored artifacts.

## Real RD-Agent Path

1. Run RD-Agent preflight:

```bash
python -m src.cli doctor --component rdagent --strict
```

2. Verify RD-Agent is installed:

```bash
rdagent collect_info
```

3. Run a health check through this project wrapper:

```bash
python -m src.cli rdagent health --execute
```

4. Run a controlled finance factor loop:

```bash
python -m src.cli rdagent run \
  --mode fin_factor \
  --loop-n 1 \
  --execute
```

Other supported modes:

```bash
python -m src.cli rdagent run --mode fin_model --loop-n 1 --execute
python -m src.cli rdagent run --mode fin_quant --loop-n 1 --execute
python -m src.cli rdagent run --mode fin_factor_report --report-folder <reports_dir> --execute
```

RD-Agent real runs write stdout/stderr logs and create experiment manifests. Generated hypotheses
must pass human review and research checks before promotion into the factor/model library.

## Troubleshooting

- If Docker commands fail, start Docker Desktop or the Docker daemon and retry `docker run
  hello-world`.
- If Qlib or LightGBM installation fails on macOS, install OpenMP with `brew install libomp`.
- If RD-Agent fails with model/provider errors, confirm `CHAT_MODEL`, `EMBEDDING_MODEL`, and the
  relevant API key/base variables match LiteLLM provider naming.
- If Qlib cannot find data, verify `qlib_init.provider_uri` points to the converted Qlib directory.
- If a result is missing, report it as unavailable. Do not infer performance from logs.

## Official References

- Qlib GitHub: https://github.com/microsoft/qlib
- Qlib quick start: https://qlib.readthedocs.io/en/stable/introduction/quick.html
- RD-Agent GitHub: https://github.com/microsoft/RD-Agent
- RD-Agent installation/configuration: https://rdagent.readthedocs.io/en/stable/installation_and_configuration.html
