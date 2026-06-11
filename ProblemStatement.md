# DoorDash Optimizer: Formal Problem Statement

## 1. Problem Data

Let

$$
R = \{1, \dots, n\}
$$

be the set of restaurants.

For each restaurant $r \in R$, let

$$
I_r = \{1, \dots, m_r\}
$$

be its item set.

For each item $i \in I_r$, define:

- $p_{ri} \ge 0$: listed price
- $k_{ri} \ge 0$: calories
- $u_{ri} \in \mathbb{Z}_{\ge 0}$: maximum allowed quantity

For each restaurant $r \in R$, define:

- $\pi_r$: promotion policy
- $d_r \ge 0$: delivery fee
- $\sigma_r \ge 0$: service fee rate
- $\tau_r \ge 0$: tax rate
- $\gamma_r \ge 0$: tip rate
- $\ell_r \ge 0$: small-order fee
- $L_r \ge 0$: small-order threshold

Global parameters:

- $B \ge 0$: user budget
- $M \in \{1, \dots, n\}$: maximum number of active restaurants

Let

$$
\pi = (\pi_1, \dots, \pi_n).
$$

## 2. Decision Variables

For each restaurant $r \in R$ and item $i \in I_r$, let:

- $x_{ri} \in \mathbb{Z}_{\ge 0}$: quantity of item $i$ purchased from restaurant $r$

For each restaurant $r \in R$, let:

- $y_r \in \{0,1\}$: restaurant activation variable

The activation constraints are:

$$
0 \le x_{ri} \le u_{ri} y_r
\qquad
\forall r \in R,\ i \in I_r
$$

Thus, if $y_r = 0$, then $x_{ri} = 0$ for every item at restaurant $r$.

Define the basket vector:

$$
x = (x_{ri})_{r \in R,\ i \in I_r}
$$

## 3. Restaurant-Level Functions

For each restaurant $r$, define the raw subtotal:

$$
S_r(x_r) = \sum_{i \in I_r} p_{ri} x_{ri}
$$

Define the calorie total:

$$
K_r(x_r) = \sum_{i \in I_r} k_{ri} x_{ri}
$$

Define total basket calories:

$$
K(x) = \sum_{r \in R} K_r(x_r)
= \sum_{r \in R} \sum_{i \in I_r} k_{ri} x_{ri}
$$

## 4. Promotion Model

For each restaurant $r$, define a discount functional:

$$
D_r(x_r; \pi_r) \ge 0
$$

This is the total discount induced by basket $x_r$ under promotion policy $\pi_r$.

Define the post-promotion subtotal:

$$
P_r(x_r; \pi_r) = S_r(x_r) - D_r(x_r; \pi_r)
$$

with feasibility condition:

$$
P_r(x_r; \pi_r) \ge 0
$$

This formulation allows `D_r` to encode BOGO rules, threshold discounts, fixed discounts, combos, exclusions, and other non-additive promotions.

### 4.1 Buy-a-Get-b Promotion

If item $i$ at restaurant $r$ follows a buy-$a$-get-$b$ rule, define the number of paid units by:

$$
g_{ri}(x_{ri})
=
a \left\lfloor \frac{x_{ri}}{a+b} \right\rfloor
+ \min(x_{ri} \bmod (a+b), a)
$$

The effective charge contributed by that item is:

$$
p_{ri} g_{ri}(x_{ri})
$$

The BOGO case corresponds to $a = 1$ and $b = 1$.

### 4.2 Threshold Percentage Discount

If restaurant $r$ offers discount rate $\delta_r$ whenever subtotal reaches threshold $T_r$, define:

$$
D_r^{\mathrm{thr}}(x_r)
=
\mathbf{1}[S_r(x_r) \ge T_r] \, \delta_r S_r(x_r)
$$

Hence:

$$
P_r(x_r; \pi_r)
=
S_r(x_r)\left(1 - \delta_r \mathbf{1}[S_r(x_r) \ge T_r]\right)
$$

### 4.3 Threshold Fixed-Dollar Discount

If restaurant $r$ offers a fixed discount $A_r$ whenever subtotal reaches threshold $T_r$, define:

$$
D_r^{\mathrm{fix}}(x_r)
=
\mathbf{1}[S_r(x_r) \ge T_r] \, A_r
$$

Hence:

$$
P_r(x_r; \pi_r) = S_r(x_r) - D_r^{\mathrm{fix}}(x_r)
$$

## 5. All-In Cost Model

For each restaurant $r$, define the all-in cost:

$$
\begin{aligned}
C_r(x_r; \pi_r)
= y_r \Big(
&P_r(x_r; \pi_r)
+ d_r
+ \sigma_r P_r(x_r; \pi_r) \\
&+ \tau_r P_r(x_r; \pi_r)
+ \gamma_r P_r(x_r; \pi_r)
+ \ell_r \mathbf{1}[P_r(x_r; \pi_r) < L_r]
\Big)
\end{aligned}
$$

Equivalently:

$$
C_r(x_r; \pi_r)
=
y_r \Big(
(1+\sigma_r+\tau_r+\gamma_r) P_r(x_r; \pi_r)
+ d_r
+ \ell_r \mathbf{1}[P_r(x_r; \pi_r) < L_r]
\Big)
$$

The total all-in basket cost is:

$$
C(x; \pi) = \sum_{r \in R} C_r(x_r; \pi_r)
$$

## 6. Feasible Set

Define the feasible set $X$ as the set of all pairs $(x, y)$ satisfying:

$$
\begin{aligned}
x_{ri} &\in \mathbb{Z}_{\ge 0} && \forall r \in R,\ i \in I_r \\
y_r &\in \{0,1\} && \forall r \in R \\
0 \le x_{ri} &\le u_{ri} y_r && \forall r \in R,\ i \in I_r \\
C(x; \pi) &\le B \\
\sum_{r \in R} y_r &\le M
\end{aligned}
$$

Thus feasibility enforces:

- item quantity bounds
- restaurant activation consistency
- budget feasibility
- a cap on the number of active restaurants

## 7. Optimization Problem

The primary objective is:

$$
\max K(x)
\quad
\text{subject to } (x,y) \in X
$$

To break ties, define the lexicographic objective:

$$
\Phi(x,y) = \left(K(x), -C(x;\pi), -\sum_{r \in R} y_r\right)
$$

The DoorDash Optimizer Problem (DOP) is:

$$
(x^*, y^*)
\in
\arg\max_{(x,y)\in X}
\left(
K(x), -C(x;\pi), -\sum_{r \in R} y_r
\right)
$$

where the objective is interpreted lexicographically.

Equivalently:

1. Maximize calories.
2. Among max-calorie baskets, minimize all-in cost.
3. Among remaining ties, minimize the number of active restaurants.

## 8. Formal Definition

Given the parameter tuple

$$
\mathcal{D}
=
\left(
R,\{I_r\}_{r \in R},p,k,u,\pi,d,\sigma,\tau,\gamma,\ell,L,B,M
\right)
$$

the DoorDash Optimizer Problem is the lexicographic integer optimization problem:

$$
(x^*, y^*)
\in
\arg\max_{(x,y)\in X}
\left(
K(x), -C(x;\pi), -\sum_{r \in R} y_r
\right)
$$

Any optimizer $(x^*, y^*)$ is called an optimal basket.

## 9. Basic Correctness Statement

Let $(x^*, y^*)$ solve DOP. Then:

$$
C(x^*; \pi) \le B
$$

and for every feasible $(x, y) \in X$:

$$
K(x^*) \ge K(x)
$$

Moreover, if $K(x) = K(x^*)$, then:

$$
C(x^*; \pi) \le C(x; \pi)
$$

Finally, if both $K(x) = K(x^*)$ and $C(x; \pi) = C(x^*; \pi)$, then:

$$
\sum_{r \in R} y_r^{*} \le \sum_{r \in R} y_r
$$

These properties follow directly from feasibility and lexicographic optimality.

## 10. Structural Properties

### 10.1 Nonlinearity

The calorie objective $K(x)$ is linear, but the cost functional $C(x; \pi)$ is generally nonlinear and may be discontinuous in the discrete decision variables.

Sources of nonlinearity include:

- threshold indicators
- buy-a-get-b staircase pricing
- restaurant activation costs
- small-order penalties

### 10.2 Threshold Activation Effect

There exist baskets $x_r$ and $x_r'$ such that:

$$
S_r(x_r') > S_r(x_r)
$$

but:

$$
P_r(x_r'; \pi_r) < P_r(x_r; \pi_r)
$$

One construction is:

- choose $x_r$ with $S_r(x_r) = T - \varepsilon$
- add a filler item of price $\varepsilon$ to obtain $x_r'$
- if the threshold discount rate is $\delta$ and $\varepsilon < T\delta$, then

$$
P_r(x_r'; \pi_r) = T(1-\delta) < T-\varepsilon = P_r(x_r; \pi_r)
$$

### 10.3 BOGO Dominance

A higher listed-price item can dominate a lower listed-price item in calories per dollar after promotions are applied.

Example:

- item A: $(p_A, k_A) = (8, 800)$
- item B: $(p_B, k_B) = (12, 1200)$

Without promotions:

$$
\frac{k_A}{p_A} = \frac{k_B}{p_B} = 100
$$

If item B is BOGO, then two units give:

$$
\text{cost} = 12,
\qquad
\text{calories} = 2400,
\qquad
\frac{2400}{12} = 200
$$

Hence item B strictly dominates item A in effective calories per dollar.

### 10.4 Restaurant Activation Cost

Opening a new restaurant is beneficial only if the extra calories gained from that restaurant justify its fixed activation cost and fee overhead.

## 11. Relation to Knapsack

If all promotions and platform fees are removed, namely:

- $D_r = 0$
- $\ell_r = 0$
- $d_r = 0$
- $\sigma_r = \tau_r = \gamma_r = 0$
- $M = n$

then DOP reduces to an integer knapsack-type model with linear costs.

In the general case, DOP is a nonlinear discrete optimization problem with:

- nonseparable promotion effects
- discontinuous threshold behavior
- fixed restaurant activation costs
- affine-plus-indicator fee transformations

## 12. Bundle Reduction Formulation

For algorithmic purposes, each restaurant may be reduced to a finite set of efficient bundles.

Let $B_r$ be the set of Pareto-undominated bundles for restaurant $r$ after internal enumeration and promotion evaluation.

For each bundle $b \in B_r$, define:

- $c_{rb}$: all-in cost
- $k_{rb}$: calories

Introduce binary variables:

- $z_{rb} \in \{0,1\}$

The reduced problem is:

$$
\begin{aligned}
\max\ &\sum_{r \in R} \sum_{b \in B_r} k_{rb} z_{rb} \\
\text{subject to }&
\sum_{r \in R} \sum_{b \in B_r} c_{rb} z_{rb} \le B, \\
&\sum_{b \in B_r} z_{rb} \le 1
\qquad \forall r \in R, \\
&\sum_{r \in R} \sum_{b \in B_r} z_{rb} \le M, \\
&z_{rb} \in \{0,1\}
\qquad \forall r \in R,\ b \in B_r
\end{aligned}
$$

This is a multiple-choice knapsack representation of the original problem after restaurant-level bundle generation.

## 13. Summary

The DoorDash Optimizer Problem is a lexicographic integer optimization problem over feasible baskets $(x, y)$. In compact form,

$$
(x^*, y^*)
\in
\arg\max_{(x,y)\in X}
\left(
K(x), -C(x;\pi), -\sum_{r \in R} y_r
\right)
$$

with lexicographic comparison of the three objective components.

The feasible set $X$ encodes:

- item quantity constraints
- promotion-dependent costs
- all-in budget feasibility
- a restaurant-count limit

Its defining feature is that the cost function is not linear in purchased quantities; instead, it is shaped by promotions, thresholds, and restaurant-level activation costs.
