/**
 * The single seeded account this build ships with.
 *
 * Google never approved Business Profile API access for this project, so there is no
 * account to create and nothing to connect: every screen reads the sample dataset that
 * is already loaded against this user. The credentials are prefilled on the sign-in form
 * and printed beside it so a reviewer on a fresh browser can still sign in. Sign-in still
 * goes through the real `/auth/login` call.
 */
export const DEMO_ACCOUNT = {
  email: "pawanpatrapp@gmail.com",
  password: "Pawan 2000",
} as const;
