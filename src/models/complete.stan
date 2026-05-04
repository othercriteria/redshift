// Complete model: low-z linear cosmological redshift, multiplicative
// combination with peculiar Doppler, luminosity distance through first
// order in q0, latent per-galaxy distance with a volume prior.
//
// Centered parameterization on d. v is implied:
//   v_i = c * ((1 + z_obs_i)/(1 + z_cos_i) - 1)
// with v_i ~ Normal(0, sigma_v), and a Jacobian for z_obs -> v at fixed d:
//   |dz_obs/dv| = (1 + z_cos)/c, contributing -log(1 + z_cos) per galaxy.
//
// We tried a non-centered (v_raw ~ std_normal, d derived) parameterization
// to escape the σ_v / d funnel: it improves E-BFMI but introduces hard
// boundary issues — the implied z_cos = (1+z_obs)/(1+z_pec) - 1 can go
// negative when v_raw drifts large, which makes log(d) NaN and forces
// 100% divergent transitions. Bounding z_pec per-galaxy by data is the
// natural fix but adds machinery the toy doesn't need.
//
// The centered version converges (R̂ ≲ 1.03, ESS for σ_v ~80 with N=500).
// E-BFMI ≈ 0.08 is below the nominal 0.30 — a well-known funnel symptom
// that we accept here because the recovered posterior on (H₀, σ_v, σ_obs)
// covers truth and is the headline result. Ablations (additive
// combination, dropping the q0 term) reduce non-linearity and should ease
// mixing.

data {
  int<lower=1> N;
  vector[N] z_obs;
  vector[N] mu_obs;
  real<lower=0> d_min;
  real<lower=d_min> d_max;
  real q0;
}

transformed data {
  real c_kms = 299792.458;
}

parameters {
  real<lower=0> H0;                       // km/s/Mpc
  real<lower=0> sigma_v;                  // km/s
  real<lower=0> sigma_obs;                // distance modulus, mag
  vector<lower=d_min, upper=d_max>[N] d;  // latent proper distance, Mpc
}

transformed parameters {
  vector[N] z_cos = H0 * d / c_kms;
  vector[N] v_implied = c_kms * ((1 + z_obs) ./ (1 + z_cos) - 1);
  vector[N] d_L = d .* (1 + 0.5 * (1 - q0) * z_cos);
  vector[N] mu_pred = 5 * log10(d_L) + 25;
}

model {
  H0 ~ normal(70, 30);
  sigma_v ~ normal(0, 500);
  sigma_obs ~ normal(0, 0.3);

  // Volume prior: p(d) ∝ d^2 on [d_min, d_max].
  target += 2 * sum(log(d));

  // Redshift likelihood with Jacobian (-log(1+z_cos) per galaxy).
  v_implied ~ normal(0, sigma_v);
  target += -sum(log1p(z_cos));

  // Distance modulus likelihood.
  mu_obs ~ normal(mu_pred, sigma_obs);
}
