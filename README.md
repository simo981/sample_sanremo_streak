# Gaussian Bet Optimizer for Sanremo T/T

**Smart combinatorial sampling for Head-to-Head (T/T) markets.**

This repository contains a Python engine designed to optimize betting strategies for binary outcome events. Instead of picking random winners or betting on favorites, this script generates the entire **phase space** of possible combinations and samples the most statistically interesting "slips" based on a target risk quantile using a **Gaussian distribution**.

## How it Works

### 1. Combinatorial Explosion
The script first generates every possible outcome for $N$ matches. Since each match is a binary event (Choice A or Choice B), the total search space $\Omega$ is defined as:

$$|\Omega| = 2^N$$

For $N=14$ matches, the system evaluates **16,384** unique combinations instantly.

### 2. The Quantile Target
We don't want the lowest payout (too safe) or the highest payout (impossible to win). We target a specific **Quantile ($Q$)** of the distribution.

Let $S$ be the sorted set of all generated slips by their total odd $O_{total}$. The script identifies a target odd $\mu$ at index $i$:

$$i = \lfloor |\Omega| \times Q_{target} \rfloor$$
$$\mu = O_{total}(S_i)$$

### 3. Gaussian Sampling
To ensure variety while staying close to our target risk, we apply a **Gaussian Weighting** function to sample slips around the target $\mu$:

$$P(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{ -\frac{1}{2}\left(\frac{x-\mu}{\sigma}\right)^2 }$$

Where:
* $\mu$ is the odd at the target quantile (e.g., Q1 for conservative play).
* $\sigma$ is derived dynamically from the local standard deviation of the odds in that region.

This ensures that the generated slips are **mathematically clustered** around your desired risk profile.

## Statistical Tuning

The algorithm is pre-configured with specific parameters to balance **precision** (hitting the target odds) and **variance** (exploring adjacent possibilities).

* **Window Radius ($R = |\Omega| / 8$):** The algorithm analyzes a local population of $|\Omega| / 8$ neighboring slips to determine the odds density.
* **StdDev Filter ($\sigma_{mul} = 4.0$):** A wide filter is applied to avoid "clipping" the Gaussian tails too early.

**The Resulting Distribution:**
This tuning creates a specific probability curve for the generated slips:
* **~60%** of slips are clustered tightly near the target quantile ($Q=0.25$).
* **~40%** are distributed on the "tails," drifting towards adjacent quantiles to capture higher variance opportunities.

## Usage

1.  Clone the repo:
    ```bash
    git clone https://github.com/simo981/sample_sanremo_streak
    ```
2.  Install dependencies:
    ```bash
    pip3 install -r requirements.txt
    ```
3. Run
   ```bash 
   python3 main.py
   ```

## Configuration

Open `main.py` and tweak the constants:

```python
SAMPLING_METHOD = "Gaussian"  # "Gaussian" or "Uniform"
QUANTILE = 0.25               # 0.25 = Safe/Medium, 0.75 = High Risk
OUTPUT_SLIPS_COUNT = 10       # How many slips to generate

# In main function (refer to Statistical Tuning)
WINDOW_RADIUS = SEARCH_SPACE / 8
STANDARD_DEV_SAMPLING = 4
```
