/**
 * Client-side resume ↔ job matching.
 *
 * Matching is done entirely in the browser against the job data already
 * loaded by SWR (JobListing objects). No extra API call is needed.
 *
 * Score breakdown (weights):
 *   Skill match   40% — overlap of candidate skills vs job's matched_keywords
 *   Role  match   30% — candidate target roles vs job title
 *   Work-mode     20% — Remote = 100, otherwise 70
 *   Experience    10% — fixed 80 (internships don't require years of exp)
 */

import type { JobListing } from "@/lib/api";

export interface CandidateProfile {
  skills: string[];
  roles: string[];
  education: string[];
  years_of_experience: number | null;
  text_length: number;
}

export interface MatchScore {
  overall: number;       // 0–100 weighted total
  skill_match: number;   // 0–100
  role_match: number;    // 0–100
  work_mode_match: number; // 0–100
  matched_skills: string[]; // profile skills found in job keywords
}

/**
 * Compute a personalised match score for one job against a candidate profile.
 */
export function matchJob(profile: CandidateProfile, job: JobListing): MatchScore {
  // ── Skill match ────────────────────────────────────────────────────────────
  const profileSkills = profile.skills.map((s) => s.toLowerCase());
  const jobKeywords = job.matched_keywords.map((k) => k.toLowerCase());

  const matchedSkills: string[] = [];
  for (const skill of profileSkills) {
    // A skill matches if it's a substring of a keyword or vice-versa
    if (jobKeywords.some((k) => k.includes(skill) || skill.includes(k))) {
      matchedSkills.push(skill);
    }
  }

  // Normalise against the smaller of: candidate's skills or 8 expected job skills
  const skillDenominator = Math.min(Math.max(profileSkills.length, 1), 8);
  const skill_match = Math.min(100, Math.round((matchedSkills.length / skillDenominator) * 100));

  // ── Role match ─────────────────────────────────────────────────────────────
  const titleLower = job.title.toLowerCase();
  const roleMatched = profile.roles.some((r) => titleLower.includes(r.toLowerCase()));
  // Partial credit if a broad role keyword appears in the title
  const broadMatch = profile.roles.some((r) => {
    const words = r.toLowerCase().split(" ");
    return words.some((w) => w.length > 4 && titleLower.includes(w));
  });
  const role_match = roleMatched ? 100 : broadMatch ? 55 : 15;

  // ── Work-mode match ────────────────────────────────────────────────────────
  const work_mode_match = job.work_mode === "Remote" ? 100 : 70;

  // ── Experience match ───────────────────────────────────────────────────────
  // Internships by definition don't require years of experience → neutral 80
  const exp_match = 80;

  // ── Overall (weighted) ────────────────────────────────────────────────────
  const overall = Math.round(
    skill_match * 0.4 +
      role_match * 0.3 +
      work_mode_match * 0.2 +
      exp_match * 0.1
  );

  return {
    overall,
    skill_match,
    role_match,
    work_mode_match,
    matched_skills: matchedSkills.slice(0, 8),
  };
}

/**
 * Compute match scores for all jobs in one pass.
 * Returns a Map<job.id, MatchScore> for O(1) lookup in the table.
 */
export function matchAllJobs(
  profile: CandidateProfile,
  jobs: JobListing[]
): Map<string, MatchScore> {
  const map = new Map<string, MatchScore>();
  for (const job of jobs) {
    map.set(job.id, matchJob(profile, job));
  }
  return map;
}
