# DoorDash Optimizer: Formal Problem Statement

## 1. Problem data

Let

$$
R = \{1,\dots,n\}
$$

be the set of restaurants. For each restaurant $r \in R$, let

$$
I_r = \{1,\dots,m_r\}
$$

be its item set.

For each item $i \in I_r$, define:

$$
p_{ri} \ge 0 \quad \text{(listed price)}
$$

$$
k_{ri} \ge 0 \quad \text{(calories)}
$$

$$
u_{ri} \in \mathbb{Z}_{\ge 0} \quad \text{(maximum allowed quantity)}
$$

For each restaurant $r \in R$, define:

$$
\pi_r \quad \text{(promotion policy)}
$$

$$
d_r \ge 0 \quad \text{(delivery fee)}
$$

$$
\sigma_r,\tau_r,\gamma_r \ge 0
\quad
\text{(service, tax, and tip rates)}
$$

$$
\ell_r \ge 0 \quad \text{(small-order fee)}
$$

$$
L_r \ge 0 \quad \text{(small-order threshold)}
$$

Global parameters:

$$
B \ge 0 \quad \text{(budget)}
$$

$$
M \in \{1,\dots,n\} \quad \text{(maximum number of active restaurants)}
$$

Let

$$
\pi = (\pi_1,\dots,\pi_n).
$$

## 2. Decision variables

For each $r \in R$ and $i \in I_r$, let

$$
x_{ri} \in \mathbb{Z}_{\ge 0}
$$

denote the number of units of item $i$ purchased from restaurant $r$.

For each restaurant $r \in R$, let

$$
y_r \in \{0,1\}
$$

indicate whether restaurant $r$ is activated.

The activation linkage is enforced by

$$
0 \le x_{ri} \le u_{ri} y_r
\qquad
\forall r \in R,\ \forall i \in I_r.
$$

Hence $y_r = 0$ implies $x_{ri} = 0$ for all $i \in I_r$.

Define the basket vector

$$
x = (x_{ri})_{r \in R,\ i \in I_r}.
$$

## 3. Restaurant-level primitives

For restaurant $r$, define the raw subtotal

$$
S_r(x_r) = \sum_{i \in I_r} p_{ri} x_{ri}
$$

and calorie total

$$
K_r(x_r) = \sum_{i \in I_r} k_{ri} x_{ri}.
$$

The total calories of the basket are

$$
K(x) = \sum_{r \in R} K_r(x_r)
= \sum_{r \in R} \sum_{i \in I_r} k_{ri} x_{ri}.
$$

## 4. Promotion model

For each restaurant $r$, define a discount functional

$$
D_r(x_r;\pi_r) \ge 0
$$

representing the total promotion value induced by basket $x_r$ under policy $\pi_r$.

The post-promotion subtotal is

$$
P_r(x_r;\pi_r) = S_r(x_r) - D_r(x_r;\pi_r),
$$

with the natural feasibility condition

$$
P_r(x_r;\pi_r) \ge 0.
$$

The formulation does not assume a specific parametric form for $D_r$. It may encode BOGO offers, threshold discounts, fixed-dollar discounts, combos, exclusions, and other non-additive promotional rules.

### 4.1. Example: buy-$a$-get-$b$

If item $i$ at restaurant $r$ follows a buy-$a$-get-$b$ rule, define the paid-unit count

$$
g_{ri}(x_{ri})
=
a \left\lfloor \frac{x_{ri}}{a+b} \right\rfloor
+ \min(x_{ri} \bmod (a+b), a).
$$

The effective charge contributed by that item is then

$$
p_{ri} g_{ri}(x_{ri}).
$$

The BOGO case is obtained by setting $a=b=1$.

### 4.2. Example: threshold percentage discount

If restaurant $r$ offers a discount of rate $\delta_r$ whenever the subtotal reaches threshold $T_r$, then

$$
D_r^{\mathrm{thr}}(x_r)
=
\mathbf{1}[S_r(x_r)\ge T_r]\,\delta_r S_r(x_r),
$$

and therefore

$$
P_r(x_r;\pi_r)
=
S_r(x_r)\left(1-\delta_r \mathbf{1}[S_r(x_r)\ge T_r]\right).
$$

### 4.3. Example: threshold fixed-dollar discount

If restaurant $r$ offers a fixed discount $A_r$ whenever the subtotal reaches threshold $T_r$, then

$$
D_r^{\mathrm{fix}}(x_r)
=
\mathbf{1}[S_r(x_r)\ge T_r]\,A_r,
$$

so that

$$
P_r(x_r;\pi_r)=S_r(x_r)-D_r^{\mathrm{fix}}(x_r).
$$

## 5. All-in cost model

For each restaurant $r$, define the all-in cost

$$
C_r(x_r;\pi_r)
=
y_r\Big(
P_r(x_r;\pi_r)
+ d_r
+ \sigma_r P_r(x_r;\pi_r)
+ \tau_r P_r(x_r;\pi_r)
+ \gamma_r P_r(x_r;\pi_r)
+ \ell_r \mathbf{1}[P_r(x_r;\pi_r)<L_r]
\Big).
$$

Equivalently,

$$
C_r(x_r;\pi_r)
=
y_r\Big(
(1+\sigma_r+\tau_r+\gamma_r)P_r(x_r;\pi_r)
+ d_r
+ \ell_r \mathbf{1}[P_r(x_r;\pi_r)<L_r]
\Big).
$$

The total all-in basket cost is

$$
C(x;\pi)=\sum_{r \in R} C_r(x_r;\pi_r).
$$

## 6. Feasible set

Define the feasible set

$$
\mathcal{X}
=
\left\{
(x,y)\,\,\middle|\,
\begin{array}{l}
x_{ri}\in \mathbb{Z}_{\ge 0},\ y_r\in\{0,1\}, \\
0\le x_{ri}\le u_{ri}y_r \quad \forall r,\forall i\in I_r, \\
C(x;\pi)\le B, \\
\sum_{r \in R} y_r \le M
\end{array}
\right\}.
$$

Thus feasibility simultaneously enforces item bounds, restaurant activation, budget, and restaurant-count limits.

## 7. Optimization problem

The primary optimization problem is

$$
\max_{(x,y)\in\mathcal{X}} K(x).
$$

To encode the preference for cheaper baskets among calorie ties, and fewer restaurants among cost ties, define the lexicographic objective

$$
\Phi(x,y)
=
\left(
K(x),
-C(x;\pi),
-\sum_{r \in R} y_r
\right).
$$

The formal DoorDash Optimizer Problem (DOP) is

$$
(x^*,y^*)
\in
\arg\max_{(x,y)\in\mathcal{X}}^{\mathrm{lex}}
\Phi(x,y).
$$

Equivalently:

1. Maximize calories.
2. Subject to maximal calories, minimize all-in cost.
3. Subject to both, minimize the number of active restaurants.

## 8. Formal definition

**Definition 1 (DoorDash Optimizer Problem).**  
Given the parameter tuple

$$
\mathcal{D}
=
\left(
R,\{I_r\}_{r\in R},p,k,u,\pi,d,\sigma,\tau,\gamma,\ell,L,B,M
\right),
$$

the DoorDash Optimizer Problem is the lexicographic integer optimization problem

$$
\max_{(x,y)\in\mathcal{X}}^{\mathrm{lex}}
\left(
K(x),
-C(x;\pi),
-\sum_{r \in R} y_r
\right).
$$

Its solution $(x^*,y^*)$ is called an optimal basket.

## 9. Basic correctness statement

**Theorem 1.**  
Let $(x^*,y^*)$ solve DOP. Then:

$$
C(x^*;\pi)\le B,
$$

$$
K(x^*) \ge K(x)
\qquad
\forall (x,y)\in\mathcal{X},
$$

and for any $(x,y)\in\mathcal{X}$ satisfying $K(x)=K(x^*)$,

$$
C(x^*;\pi)\le C(x;\pi).
$$

Further, for any $(x,y)\in\mathcal{X}$ satisfying both

$$
K(x)=K(x^*)
\quad\text{and}\quad
C(x;\pi)=C(x^*;\pi),
$$

we have

$$
\sum_{r \in R} y_r^*
\le
\sum_{r \in R} y_r.
$$

**Proof.**  
All claims follow immediately from feasibility of $(x^*,y^*)$ and lexicographic optimality of $\Phi(x,y)$ over $\mathcal{X}$. $\square$

## 10. Structural properties

### Proposition 1. Nonlinearity

The objective component $K(x)$ is linear, but the feasible-cost map $C(x;\pi)$ is generally nonlinear and may be discontinuous in the discrete variables.

**Reason.**  
Threshold promotions create indicator jumps, buy-$a$-get-$b$ rules create staircase pricing, and restaurant activation introduces fixed costs.

### Proposition 2. Threshold activation effect

There exist baskets $x_r,x_r'$ such that

$$
S_r(x_r') > S_r(x_r)
$$

but

$$
P_r(x_r';\pi_r) < P_r(x_r;\pi_r).
$$

**Construction.**  
Let $S_r(x_r)=T-\varepsilon$ for some threshold $T$ and $\varepsilon>0$, and add a filler item of price $\varepsilon$ to obtain $x_r'$. If the threshold discount rate is $\delta$ and $\varepsilon<T\delta$, then

$$
P_r(x_r';\pi_r)=T(1-\delta)<T-\varepsilon=P_r(x_r;\pi_r).
$$

### Proposition 3. BOGO dominance

A higher listed-price item can dominate a lower listed-price item in calories per dollar after promotions are applied.

**Example.**  
Let item A have $(p_A,k_A)=(8,800)$ and item B have $(p_B,k_B)=(12,1200)$. Without promotions,

$$
\frac{k_A}{p_A}=\frac{k_B}{p_B}=100.
$$

If B is BOGO, then purchasing two units yields

$$
\text{cost}=12,\qquad \text{calories}=2400,
$$

hence

$$
\frac{2400}{12}=200>100.
$$

### Proposition 4. Restaurant activation cost

Opening a new restaurant is beneficial only if the incremental calories obtained from that restaurant justify its incremental fixed activation cost.

Formally, if restaurant $s$ is inactive in basket $x$ and activated in basket $x'$, then the gain is justified only if the additional calorie return from the induced sub-basket at $s$ dominates alternative uses of the same remaining budget within currently active restaurants.

## 11. Relation to knapsack

If $D_r \equiv 0$, $\ell_r=0$, $d_r=0$, $\sigma_r=\tau_r=\gamma_r=0$, and $M=n$, then DOP reduces to an integer knapsack-type model with separable linear costs.

In the general case, DOP is more accurately described as a nonlinear discrete optimization problem with:

- nonseparable promotion effects,
- discontinuous threshold behavior,
- fixed restaurant activation costs, and
- platform-induced affine-plus-indicator cost transformations.

## 12. Bundle reduction formulation

For algorithmic purposes, each restaurant may be reduced to a finite set of efficient bundles. Let

$$
\mathcal{B}_r
$$

denote the set of Pareto-undominated bundles for restaurant $r$ after internal enumeration and promotion evaluation.

For each $b \in \mathcal{B}_r$, define:

$$
c_{rb} \quad \text{(all-in cost)}, \qquad k_{rb} \quad \text{(calories)}.
$$

Introduce binary selection variables

$$
z_{rb}\in\{0,1\}.
$$

Then the reduced global problem is

$$
\max \sum_{r \in R}\sum_{b \in \mathcal{B}_r} k_{rb} z_{rb}
$$

subject to

$$
\sum_{r \in R}\sum_{b \in \mathcal{B}_r} c_{rb} z_{rb}\le B,
$$

$$
\sum_{b \in \mathcal{B}_r} z_{rb}\le 1
\qquad
\forall r \in R,
$$

$$
\sum_{r \in R}\sum_{b \in \mathcal{B}_r} z_{rb} \le M,
$$

$$
z_{rb}\in\{0,1\}.
$$

This is a multiple-choice knapsack representation of the original problem after restaurant-level bundle generation.

## 13. Summary

The DoorDash Optimizer Problem is the lexicographic integer optimization problem

$$
\max^{\mathrm{lex}}
\left(
K(x),
-C(x;\pi),
-\sum_{r \in R} y_r
\right)
$$

over the feasible set $\mathcal{X}$ induced by menu quantities, promotion rules, budget, and restaurant activation constraints. Its distinguishing feature is that the cost functional is not linear in purchased quantities; rather, it is shaped by promotions, fixed fees, and threshold effects at the restaurant level.
