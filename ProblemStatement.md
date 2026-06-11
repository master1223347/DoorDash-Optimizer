# DoorDash Optimizer: Formal Problem Statement

## 1. Problem Data

Let `R = {1, ..., n}` be the set of restaurants.

For each restaurant `r in R`, let `I_r = {1, ..., m_r}` be its item set.

For each item `i in I_r`, define:

- `p_ri >= 0`: listed price
- `k_ri >= 0`: calories
- `u_ri in Z_nonnegative`: maximum allowed quantity

For each restaurant `r in R`, define:

- `pi_r`: promotion policy
- `d_r >= 0`: delivery fee
- `sigma_r >= 0`: service fee rate
- `tau_r >= 0`: tax rate
- `gamma_r >= 0`: tip rate
- `ell_r >= 0`: small-order fee
- `L_r >= 0`: small-order threshold

Global parameters:

- `B >= 0`: user budget
- `M in {1, ..., n}`: maximum number of active restaurants

Let `pi = (pi_1, ..., pi_n)`.

## 2. Decision Variables

For each restaurant `r in R` and item `i in I_r`, let:

- `x_ri in Z_nonnegative`: quantity of item `i` purchased from restaurant `r`

For each restaurant `r in R`, let:

- `y_r in {0, 1}`: restaurant activation variable

The activation constraints are:

```text
0 <= x_ri <= u_ri y_r    for all r in R, i in I_r
```

Thus, if `y_r = 0`, then `x_ri = 0` for every item at restaurant `r`.

Define the basket vector:

```text
x = (x_ri) over all r in R and i in I_r
```

## 3. Restaurant-Level Functions

For each restaurant `r`, define the raw subtotal:

```text
S_r(x_r) = sum_{i in I_r} p_ri x_ri
```

Define the calorie total:

```text
K_r(x_r) = sum_{i in I_r} k_ri x_ri
```

Define total basket calories:

```text
K(x) = sum_{r in R} K_r(x_r)
     = sum_{r in R} sum_{i in I_r} k_ri x_ri
```

## 4. Promotion Model

For each restaurant `r`, define a discount functional:

```text
D_r(x_r; pi_r) >= 0
```

This is the total discount induced by basket `x_r` under promotion policy `pi_r`.

Define the post-promotion subtotal:

```text
P_r(x_r; pi_r) = S_r(x_r) - D_r(x_r; pi_r)
```

with feasibility condition:

```text
P_r(x_r; pi_r) >= 0
```

This formulation allows `D_r` to encode BOGO rules, threshold discounts, fixed discounts, combos, exclusions, and other non-additive promotions.

### 4.1 Buy-a-Get-b Promotion

If item `i` at restaurant `r` follows a buy-`a`-get-`b` rule, define the number of paid units by:

```text
g_ri(x_ri) = a * floor(x_ri / (a + b)) + min(x_ri mod (a + b), a)
```

The effective charge contributed by that item is:

```text
p_ri g_ri(x_ri)
```

The BOGO case corresponds to `a = 1` and `b = 1`.

### 4.2 Threshold Percentage Discount

If restaurant `r` offers discount rate `delta_r` whenever subtotal reaches threshold `T_r`, define:

```text
D_r^thr(x_r) = 1[S_r(x_r) >= T_r] * delta_r * S_r(x_r)
```

Hence:

```text
P_r(x_r; pi_r) = S_r(x_r) * (1 - delta_r * 1[S_r(x_r) >= T_r])
```

### 4.3 Threshold Fixed-Dollar Discount

If restaurant `r` offers a fixed discount `A_r` whenever subtotal reaches threshold `T_r`, define:

```text
D_r^fix(x_r) = 1[S_r(x_r) >= T_r] * A_r
```

Hence:

```text
P_r(x_r; pi_r) = S_r(x_r) - D_r^fix(x_r)
```

## 5. All-In Cost Model

For each restaurant `r`, define the all-in cost:

```text
C_r(x_r; pi_r)
  = y_r * (
      P_r(x_r; pi_r)
      + d_r
      + sigma_r P_r(x_r; pi_r)
      + tau_r P_r(x_r; pi_r)
      + gamma_r P_r(x_r; pi_r)
      + ell_r * 1[P_r(x_r; pi_r) < L_r]
    )
```

Equivalently:

```text
C_r(x_r; pi_r)
  = y_r * (
      (1 + sigma_r + tau_r + gamma_r) P_r(x_r; pi_r)
      + d_r
      + ell_r * 1[P_r(x_r; pi_r) < L_r]
    )
```

The total all-in basket cost is:

```text
C(x; pi) = sum_{r in R} C_r(x_r; pi_r)
```

## 6. Feasible Set

Define the feasible set `X` as the set of all pairs `(x, y)` satisfying:

```text
x_ri in Z_nonnegative                  for all r in R, i in I_r
y_r in {0, 1}                         for all r in R
0 <= x_ri <= u_ri y_r                 for all r in R, i in I_r
C(x; pi) <= B
sum_{r in R} y_r <= M
```

Thus feasibility enforces:

- item quantity bounds
- restaurant activation consistency
- budget feasibility
- a cap on the number of active restaurants

## 7. Optimization Problem

The primary objective is:

```text
maximize K(x)
subject to (x, y) in X
```

To break ties, define the lexicographic objective:

```text
Phi(x, y) = ( K(x), -C(x; pi), -sum_{r in R} y_r )
```

The DoorDash Optimizer Problem (DOP) is:

```text
lexicographically maximize Phi(x, y)
subject to (x, y) in X
```

Equivalently:

1. Maximize calories.
2. Among max-calorie baskets, minimize all-in cost.
3. Among remaining ties, minimize the number of active restaurants.

## 8. Formal Definition

Given the parameter tuple

```text
D = (R, (I_r for r in R), p, k, u, pi, d, sigma, tau, gamma, ell, L, B, M)
```

the DoorDash Optimizer Problem is the lexicographic integer optimization problem:

```text
maximize ( K(x), -C(x; pi), -sum_{r in R} y_r )
subject to (x, y) in X
```

Any optimizer `(x*, y*)` is called an optimal basket.

## 9. Basic Correctness Statement

Let `(x*, y*)` solve DOP. Then:

```text
C(x*; pi) <= B
```

and for every feasible `(x, y) in X`:

```text
K(x*) >= K(x)
```

Moreover, if `K(x) = K(x*)`, then:

```text
C(x*; pi) <= C(x; pi)
```

Finally, if both `K(x) = K(x*)` and `C(x; pi) = C(x*; pi)`, then:

```text
sum_{r in R} y_r_star <= sum_{r in R} y_r
```

These properties follow directly from feasibility and lexicographic optimality.

## 10. Structural Properties

### 10.1 Nonlinearity

The calorie objective `K(x)` is linear, but the cost functional `C(x; pi)` is generally nonlinear and may be discontinuous in the discrete decision variables.

Sources of nonlinearity include:

- threshold indicators
- buy-a-get-b staircase pricing
- restaurant activation costs
- small-order penalties

### 10.2 Threshold Activation Effect

There exist baskets `x_r` and `x_r'` such that:

```text
S_r(x_r') > S_r(x_r)
```

but:

```text
P_r(x_r'; pi_r) < P_r(x_r; pi_r)
```

One construction is:

- choose `x_r` with `S_r(x_r) = T - epsilon`
- add a filler item of price `epsilon` to obtain `x_r'`
- if the threshold discount rate is `delta` and `epsilon < T delta`, then

```text
P_r(x_r'; pi_r) = T(1 - delta) < T - epsilon = P_r(x_r; pi_r)
```

### 10.3 BOGO Dominance

A higher listed-price item can dominate a lower listed-price item in calories per dollar after promotions are applied.

Example:

- item A: `(p_A, k_A) = (8, 800)`
- item B: `(p_B, k_B) = (12, 1200)`

Without promotions:

```text
k_A / p_A = k_B / p_B = 100
```

If item B is BOGO, then two units give:

```text
cost = 12
calories = 2400
calories per dollar = 2400 / 12 = 200
```

Hence item B strictly dominates item A in effective calories per dollar.

### 10.4 Restaurant Activation Cost

Opening a new restaurant is beneficial only if the extra calories gained from that restaurant justify its fixed activation cost and fee overhead.

## 11. Relation to Knapsack

If all promotions and platform fees are removed, namely:

- `D_r = 0`
- `ell_r = 0`
- `d_r = 0`
- `sigma_r = tau_r = gamma_r = 0`
- `M = n`

then DOP reduces to an integer knapsack-type model with linear costs.

In the general case, DOP is a nonlinear discrete optimization problem with:

- nonseparable promotion effects
- discontinuous threshold behavior
- fixed restaurant activation costs
- affine-plus-indicator fee transformations

## 12. Bundle Reduction Formulation

For algorithmic purposes, each restaurant may be reduced to a finite set of efficient bundles.

Let `B_r` be the set of Pareto-undominated bundles for restaurant `r` after internal enumeration and promotion evaluation.

For each bundle `b in B_r`, define:

- `c_rb`: all-in cost
- `k_rb`: calories

Introduce binary variables:

- `z_rb in {0, 1}`

The reduced problem is:

```text
maximize sum_{r in R} sum_{b in B_r} k_rb z_rb
subject to
sum_{r in R} sum_{b in B_r} c_rb z_rb <= B
sum_{b in B_r} z_rb <= 1                  for all r in R
sum_{r in R} sum_{b in B_r} z_rb <= M
z_rb in {0, 1}                            for all r in R, b in B_r
```

This is a multiple-choice knapsack representation of the original problem after restaurant-level bundle generation.

## 13. Summary

The DoorDash Optimizer Problem is a lexicographic integer optimization problem over feasible baskets `(x, y)` with objective:

```text
( K(x), -C(x; pi), -sum_{r in R} y_r )
```

subject to:

- item quantity constraints
- promotion-dependent costs
- all-in budget feasibility
- a restaurant-count limit

Its defining feature is that the cost function is not linear in purchased quantities; instead, it is shaped by promotions, thresholds, and restaurant-level activation costs.
