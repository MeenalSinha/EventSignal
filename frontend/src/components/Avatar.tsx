import React from "react";

// ============================================================================
// HASH HELPER FOR DETERMINISTIC AVATAR ATTRIBUTES
// ============================================================================
function getHash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

// ============================================================================
// 1. OPPORTUNITY & EVENT AVATAR
// Replaces the empty thumbnail block [S] INTERNSHIP / [A] HACKATHON with a rich,
// beautifully illustrated SVG avatar representing the opportunity.
// ============================================================================

export interface OpportunityAvatarProps {
  title: string;
  opportunityType?: string | null | undefined;
  organizer?: string | null | undefined;
  size?: "sm" | "md" | "lg" | undefined;
  className?: string | undefined;
  src?: string | null | undefined;
}

export const OpportunityAvatar: React.FC<OpportunityAvatarProps> = ({
  title,
  opportunityType = "event",
  organizer = "",
  size = "lg",
  className = "",
  src = null,
}) => {
  const [imgError, setImgError] = React.useState(false);

  if (src && !imgError) {
    const sizeClasses =
      size === "sm"
        ? "h-10 w-10 rounded-xl"
        : size === "md"
        ? "h-16 w-16 rounded-xl"
        : "h-24 w-24 sm:h-28 sm:w-28 rounded-2xl";
    return (
      <div
        className={`relative shrink-0 overflow-hidden border border-slate-200/80 bg-slate-100 shadow-xs ${sizeClasses} ${className}`}
        title={title}
      >
        <img
          src={src}
          alt={title}
          className="h-full w-full object-cover"
          onError={() => setImgError(true)}
          loading="lazy"
        />
      </div>
    );
  }

  const normType = (opportunityType || "event").toLowerCase();
  const seed = getHash(`${title}-${normType}-${organizer}`);

  // Category determination
  const isHackathon =
    normType.includes("hack") ||
    normType.includes("code") ||
    title.toLowerCase().includes("hackathon");
  const isInternship =
    normType.includes("intern") ||
    normType.includes("job") ||
    normType.includes("career") ||
    title.toLowerCase().includes("intern");
  const isWorkshop =
    normType.includes("workshop") ||
    normType.includes("talk") ||
    normType.includes("conference") ||
    title.toLowerCase().includes("workshop");
  const isResearch =
    normType.includes("research") ||
    normType.includes("fellowship") ||
    normType.includes("grant") ||
    title.toLowerCase().includes("research");
  const isSprint =
    normType.includes("sprint") ||
    normType.includes("challenge") ||
    normType.includes("competition") ||
    title.toLowerCase().includes("sprint");

  // Visual Theme Palettes (Tailwind gradients and SVG colors)
  let theme = {
    bgGradient: "from-indigo-500/15 via-purple-500/20 to-indigo-600/30",
    border: "border-indigo-200/80",
    badgeBg: "bg-indigo-600 text-white",
    iconColor: "#6366F1",
    accentColor: "#A855F7",
    categoryLabel: "Hackathon",
  };

  if (isInternship) {
    theme = {
      bgGradient: "from-emerald-500/15 via-teal-500/20 to-emerald-600/30",
      border: "border-emerald-200/80",
      badgeBg: "bg-emerald-700 text-white",
      iconColor: "#059669",
      accentColor: "#0D9488",
      categoryLabel: "Internship",
    };
  } else if (isWorkshop) {
    theme = {
      bgGradient: "from-amber-500/15 via-orange-500/20 to-amber-600/30",
      border: "border-amber-200/80",
      badgeBg: "bg-amber-600 text-white",
      iconColor: "#D97706",
      accentColor: "#EA580C",
      categoryLabel: "Workshop",
    };
  } else if (isResearch) {
    theme = {
      bgGradient: "from-sky-500/15 via-blue-500/20 to-cyan-600/30",
      border: "border-sky-200/80",
      badgeBg: "bg-sky-600 text-white",
      iconColor: "#0284C7",
      accentColor: "#2563EB",
      categoryLabel: "Research",
    };
  } else if (isSprint) {
    theme = {
      bgGradient: "from-rose-500/15 via-pink-500/20 to-rose-600/30",
      border: "border-rose-200/80",
      badgeBg: "bg-rose-600 text-white",
      iconColor: "#E11D48",
      accentColor: "#DB2777",
      categoryLabel: "Sprint",
    };
  } else if (!isHackathon) {
    // Default campus event / opportunity
    theme = {
      bgGradient: "from-teal-500/15 via-cyan-500/20 to-slate-600/25",
      border: "border-teal-200/80",
      badgeBg: "bg-teal-700 text-white",
      iconColor: "#0D9488",
      accentColor: "#0891B2",
      categoryLabel: (opportunityType || "Event").replace("_", " "),
    };
  }

  // Small size (e.g. for sidebar widgets)
  if (size === "sm") {
    return (
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${theme.border} bg-gradient-to-br ${theme.bgGradient} shadow-2xs overflow-hidden relative ${className}`}
        title={`${title} (${theme.categoryLabel})`}
      >
        <svg
          viewBox="0 0 40 40"
          className="h-7 w-7 transition transform group-hover:scale-105"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {isHackathon && (
            <g>
              <circle cx="20" cy="15" r="7" fill={theme.iconColor} opacity="0.85" />
              <rect x="13" y="14" width="14" height="3" rx="1.5" fill="#1E1B4B" />
              <path
                d="M10 29C10 24 14.5 22 20 22C25.5 22 30 24 30 29"
                stroke={theme.iconColor}
                strokeWidth="2.5"
                strokeLinecap="round"
              />
              <path d="M16 26L14 28L16 30M24 26L26 28L24 30" stroke="#FFF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </g>
          )}
          {isInternship && (
            <g>
              <circle cx="20" cy="14" r="6.5" fill={theme.iconColor} opacity="0.85" />
              <path d="M12 28C12 23 15.5 21 20 21C24.5 21 28 23 28 28" fill={theme.iconColor} opacity="0.4" />
              <rect x="15" y="24" width="10" height="7" rx="1.5" fill={theme.accentColor} />
              <path d="M18 24V22.5C18 22 18.5 21.5 19 21.5H21C21.5 21.5 22 22 22 22.5V24" stroke="#FFF" strokeWidth="1" />
            </g>
          )}
          {isWorkshop && (
            <g>
              <circle cx="20" cy="15" r="6.5" fill={theme.iconColor} opacity="0.85" />
              <path d="M11 29C11 24 15 22 20 22C25 22 29 24 29 29" stroke={theme.iconColor} strokeWidth="2.5" strokeLinecap="round" />
              <circle cx="28" cy="12" r="3.5" fill="#F59E0B" />
              <path d="M28 10V14M26 12H30" stroke="#FFF" strokeWidth="1" strokeLinecap="round" />
            </g>
          )}
          {isResearch && (
            <g>
              <circle cx="20" cy="14" r="6" fill={theme.iconColor} opacity="0.85" />
              <path d="M14 10L20 7L26 10L20 13L14 10Z" fill="#0369A1" />
              <path d="M26 10V14" stroke="#0369A1" strokeWidth="1.5" strokeLinecap="round" />
              <path d="M12 28C12 23.5 15.5 21.5 20 21.5C24.5 21.5 28 23.5 28 28" stroke={theme.iconColor} strokeWidth="2.2" strokeLinecap="round" />
            </g>
          )}
          {isSprint && (
            <g>
              <path d="M20 7C22 11 25 15 24 20C23 23 20 25 20 25C20 25 17 23 16 20C15 15 18 11 20 7Z" fill={theme.iconColor} />
              <circle cx="20" cy="16" r="2.5" fill="#FFF" />
              <path d="M16 20L13 22M24 20L27 22" stroke={theme.accentColor} strokeWidth="2" strokeLinecap="round" />
              <path d="M19 25L17 28M21 25L23 28" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" />
            </g>
          )}
          {!isHackathon && !isInternship && !isWorkshop && !isResearch && !isSprint && (
            <g>
              <circle cx="20" cy="15" r="6.5" fill={theme.iconColor} opacity="0.9" />
              <path d="M11 28C11 23.5 15 21.5 20 21.5C25 21.5 29 23.5 29 28" stroke={theme.iconColor} strokeWidth="2.5" strokeLinecap="round" />
              <path d="M20 18V21M17 19.5H23" stroke="#FFF" strokeWidth="1.2" strokeLinecap="round" />
            </g>
          )}
        </svg>
      </div>
    );
  }

  // Large size (Primary feed card thumbnail: 96px x 96px or 112px x 112px)
  return (
    <div
      className={`relative flex h-24 w-24 sm:h-28 sm:w-28 shrink-0 flex-col items-center justify-between rounded-2xl border ${theme.border} bg-gradient-to-br ${theme.bgGradient} p-2 shadow-xs transition hover:shadow-md overflow-hidden ${className}`}
      title={`${title} (${theme.categoryLabel})`}
    >
      {/* Decorative ambient background rings */}
      <div className="absolute -top-6 -right-6 h-16 w-16 rounded-full bg-white/20 blur-xs pointer-events-none" />
      <div className="absolute -bottom-8 -left-8 h-20 w-20 rounded-full bg-white/30 blur-xs pointer-events-none" />

      {/* Main Avatar Illustration Canvas */}
      <div className="relative flex-1 flex items-center justify-center w-full pt-1">
        <svg
          viewBox="0 0 80 72"
          className="h-16 w-16 sm:h-18 sm:w-18 drop-shadow-sm transition transform group-hover:scale-105"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* DEFINITIONS & GRADIENTS */}
          <defs>
            <linearGradient id={`grad-skin-${seed}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FBD7B5" />
              <stop offset="100%" stopColor="#F5B98A" />
            </linearGradient>
            <linearGradient id={`grad-hair-${seed}`} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#1E293B" />
              <stop offset="100%" stopColor="#0F172A" />
            </linearGradient>
            <linearGradient id={`grad-accent-${seed}`} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={theme.iconColor} />
              <stop offset="100%" stopColor={theme.accentColor} />
            </linearGradient>
          </defs>

          {/* 1. HACKATHON AVATAR: Tech coder with glasses & glowing laptop screen */}
          {isHackathon && (
            <g>
              {/* Shoulders & Hoodie */}
              <path
                d="M16 68C16 52 26 46 40 46C54 46 64 52 64 68"
                fill={`url(#grad-accent-${seed})`}
              />
              <path
                d="M32 46L40 56L48 46"
                stroke="#FFF"
                strokeWidth="2"
                strokeLinecap="round"
                opacity="0.8"
              />
              {/* Neck & Head */}
              <rect x="36" y="38" width="8" height="10" rx="3" fill={`url(#grad-skin-${seed})`} />
              <circle cx="40" cy="27" r="14" fill={`url(#grad-skin-${seed})`} />
              {/* Hair (Cool Beanie / Modern Cut) */}
              <path
                d="M26 24C26 15 32 11 40 11C48 11 54 15 54 24C50 20 44 21 40 21C35 21 30 20 26 24Z"
                fill={`url(#grad-hair-${seed})`}
              />
              {/* Coder Glasses */}
              <rect x="30" y="24" width="8" height="6" rx="2" fill="#0F172A" />
              <rect x="42" y="24" width="8" height="6" rx="2" fill="#0F172A" />
              <line x1="38" y1="27" x2="42" y2="27" stroke="#0F172A" strokeWidth="2" />
              <line x1="31" y1="26" x2="35" y2="28" stroke="#38BDF8" strokeWidth="1" />
              <line x1="43" y1="26" x2="47" y2="28" stroke="#38BDF8" strokeWidth="1" />
              {/* Smiling mouth */}
              <path d="M37 34C38.5 36 41.5 36 43 34" stroke="#7C2D12" strokeWidth="1.5" strokeLinecap="round" />
              {/* Glowing Code Screen Symbol in Front */}
              <rect x="26" y="56" width="28" height="15" rx="3" fill="#090D16" stroke="#4F46E5" strokeWidth="1.5" />
              <path d="M33 61L30 63.5L33 66M47 61L50 63.5L47 66M42 59L38 68" stroke="#38BDF8" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
            </g>
          )}

          {/* 2. INTERNSHIP AVATAR: Professional student intern with collar, lanyard & star */}
          {isInternship && (
            <g>
              {/* Blazer / Collared Shirt */}
              <path
                d="M16 68C16 52 26 46 40 46C54 46 64 52 64 68"
                fill={`url(#grad-accent-${seed})`}
              />
              {/* White Collared Shirt V */}
              <path d="M34 46L40 56L46 46" fill="#FFF" />
              <path d="M39 50L40 58L41 50" fill="#0D9488" />
              {/* Head & Neck */}
              <rect x="36" y="38" width="8" height="10" rx="3" fill={`url(#grad-skin-${seed})`} />
              <circle cx="40" cy="27" r="14" fill={`url(#grad-skin-${seed})`} />
              {/* Professional Hairstyle */}
              <path
                d="M26 23C26 14 31 10 40 10C49 10 54 14 54 23C51 18 45 17 40 17C34 17 29 19 26 23Z"
                fill="#422006"
              />
              {/* Eyes & Warm Smile */}
              <circle cx="35" cy="27" r="1.8" fill="#1C1917" />
              <circle cx="45" cy="27" r="1.8" fill="#1C1917" />
              <path d="M36 33C38 35.5 42 35.5 44 33" stroke="#7C2D12" strokeWidth="1.8" strokeLinecap="round" />
              {/* Lanyard & ID Badge */}
              <path d="M36 46L38 56M44 46L42 56" stroke="#F59E0B" strokeWidth="1.5" />
              <rect x="35" y="56" width="10" height="13" rx="2" fill="#FFF" stroke="#CBD5E1" strokeWidth="1" />
              <circle cx="40" cy="60" r="1.8" fill="#059669" />
              <line x1="37" y1="64" x2="43" y2="64" stroke="#94A3B8" strokeWidth="1" strokeLinecap="round" />
              {/* Star of Merit Badge */}
              <circle cx="58" cy="22" r="7" fill="#FBBF24" />
              <path d="M58 18L59.2 20.8L62 21.2L60 23L60.5 26L58 24.5L55.5 26L56 23L54 21.2L56.8 20.8L58 18Z" fill="#FFF" />
            </g>
          )}

          {/* 3. WORKSHOP / CAMPUS TALK AVATAR: Dynamic speaker with microphone & spark */}
          {isWorkshop && (
            <g>
              {/* Casual smart jacket */}
              <path
                d="M16 68C16 52 26 46 40 46C54 46 64 52 64 68"
                fill={`url(#grad-accent-${seed})`}
              />
              <path d="M35 46L40 54L45 46" fill="#FFF" />
              {/* Head & Neck */}
              <rect x="36" y="38" width="8" height="10" rx="3" fill={`url(#grad-skin-${seed})`} />
              <circle cx="40" cy="27" r="14" fill={`url(#grad-skin-${seed})`} />
              {/* Modern Curly / Textured Hair */}
              <path
                d="M26 24C24 16 31 10 40 10C49 10 56 16 54 24C52 18 47 17 40 17C33 17 28 19 26 24Z"
                fill="#18181B"
              />
              <circle cx="28" cy="18" r="4" fill="#18181B" />
              <circle cx="52" cy="18" r="4" fill="#18181B" />
              <circle cx="40" cy="11" r="4" fill="#18181B" />
              {/* Eyes & Speaking Smile */}
              <circle cx="35" cy="26" r="1.8" fill="#1C1917" />
              <circle cx="45" cy="26" r="1.8" fill="#1C1917" />
              <path d="M36 32C37.5 35 42.5 35 44 32" stroke="#7C2D12" strokeWidth="2" strokeLinecap="round" />
              {/* Handheld Microphone */}
              <rect x="48" y="44" width="7" height="14" rx="3.5" fill="#334155" />
              <rect x="49" y="44" width="5" height="7" rx="2.5" fill="#94A3B8" />
              <line x1="51.5" y1="58" x2="51.5" y2="65" stroke="#475569" strokeWidth="2" />
              {/* Lightbulb of Knowledge */}
              <circle cx="22" cy="20" r="7" fill="#FDE047" />
              <path d="M22 17V23M19 20H25" stroke="#CA8A04" strokeWidth="1.5" strokeLinecap="round" />
            </g>
          )}

          {/* 4. RESEARCH / FELLOWSHIP AVATAR: Scholar with academic cap & atom badge */}
          {isResearch && (
            <g>
              {/* Academic Robe / Gown */}
              <path
                d="M16 68C16 52 26 46 40 46C54 46 64 52 64 68"
                fill={`url(#grad-accent-${seed})`}
              />
              <path d="M38 46L40 68L42 46" stroke="#F59E0B" strokeWidth="2" />
              {/* Head & Neck */}
              <rect x="36" y="38" width="8" height="10" rx="3" fill={`url(#grad-skin-${seed})`} />
              <circle cx="40" cy="29" r="13" fill={`url(#grad-skin-${seed})`} />
              {/* Academic Graduation Cap (Mortarboard) */}
              <path d="M18 19L40 10L62 19L40 28L18 19Z" fill="#0C4A6E" />
              <rect x="30" y="24" width="20" height="6" fill="#075985" />
              <circle cx="40" cy="19" r="2.5" fill="#F59E0B" />
              <path d="M40 19L57 26V35" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" />
              {/* Wire-frame Round Spectacles */}
              <circle cx="35" cy="29" r="4.5" stroke="#0284C7" strokeWidth="1.5" fill="#FFF" fillOpacity="0.4" />
              <circle cx="45" cy="29" r="4.5" stroke="#0284C7" strokeWidth="1.5" fill="#FFF" fillOpacity="0.4" />
              <line x1="39.5" y1="29" x2="40.5" y2="29" stroke="#0284C7" strokeWidth="1.5" />
              <path d="M38 36C39.2 37.2 40.8 37.2 42 36" stroke="#7C2D12" strokeWidth="1.5" strokeLinecap="round" />
              {/* Atom / Discovery Emblem */}
              <ellipse cx="60" cy="50" rx="8" ry="4" stroke="#38BDF8" strokeWidth="1.2" transform="rotate(30 60 50)" />
              <ellipse cx="60" cy="50" rx="8" ry="4" stroke="#38BDF8" strokeWidth="1.2" transform="rotate(-30 60 50)" />
              <circle cx="60" cy="50" r="2" fill="#0284C7" />
            </g>
          )}

          {/* 5. SPRINT / COMPETITION AVATAR: Fast innovator with launch rocket badge */}
          {isSprint && (
            <g>
              {/* Athletic Sprint Jacket */}
              <path
                d="M16 68C16 52 26 46 40 46C54 46 64 52 64 68"
                fill={`url(#grad-accent-${seed})`}
              />
              <path d="M37 46V68M43 46V68" stroke="#FFF" strokeWidth="1.5" opacity="0.8" />
              {/* Head & Neck */}
              <rect x="36" y="38" width="8" height="10" rx="3" fill={`url(#grad-skin-${seed})`} />
              <circle cx="40" cy="27" r="14" fill={`url(#grad-skin-${seed})`} />
              {/* Headband & Hair */}
              <path
                d="M26 23C26 14 31 10 40 10C49 10 54 14 54 23Z"
                fill="#312E81"
              />
              <rect x="26" y="19" width="28" height="5" rx="2" fill="#E11D48" />
              {/* Eyes & Determined Expression */}
              <circle cx="35" cy="27" r="1.8" fill="#1C1917" />
              <circle cx="45" cy="27" r="1.8" fill="#1C1917" />
              <path d="M36 33C38 35 42 35 44 33" stroke="#7C2D12" strokeWidth="1.8" strokeLinecap="round" />
              {/* Rocket Badge */}
              <g transform="translate(48, 8) scale(0.7)">
                <path d="M15 2C18 7 21 12 20 18C18 21 15 23 15 23C15 23 12 21 10 18C9 12 12 7 15 2Z" fill="#F43F5E" />
                <circle cx="15" cy="11" r="2.5" fill="#FFF" />
                <path d="M10 18L7 21M20 18L23 21" stroke="#E11D48" strokeWidth="2" strokeLinecap="round" />
                <path d="M14 23L12 27M16 23L18 27" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" />
              </g>
            </g>
          )}

          {/* 6. GENERAL EVENT AVATAR: Friendly community explorer */}
          {!isHackathon && !isInternship && !isWorkshop && !isResearch && !isSprint && (
            <g>
              {/* Casual Campus Sweater */}
              <path
                d="M16 68C16 52 26 46 40 46C54 46 64 52 64 68"
                fill={`url(#grad-accent-${seed})`}
              />
              <circle cx="40" cy="46" r="5" fill="#FFF" opacity="0.3" />
              {/* Head & Neck */}
              <rect x="36" y="38" width="8" height="10" rx="3" fill={`url(#grad-skin-${seed})`} />
              <circle cx="40" cy="27" r="14" fill={`url(#grad-skin-${seed})`} />
              {/* Casual Styled Hair */}
              <path
                d="M26 23C26 14 31 10 40 10C49 10 54 14 54 23C51 18 45 17 40 17C34 17 29 19 26 23Z"
                fill="#292524"
              />
              {/* Friendly Eyes & Bright Smile */}
              <circle cx="35" cy="27" r="1.8" fill="#1C1917" />
              <circle cx="45" cy="27" r="1.8" fill="#1C1917" />
              <path d="M36 33C38 35.5 42 35.5 44 33" stroke="#7C2D12" strokeWidth="2" strokeLinecap="round" />
              {/* Opportunity Sparkle Badge */}
              <circle cx="58" cy="22" r="6" fill="#14B8A6" />
              <path d="M58 18V26M54 22H62" stroke="#FFF" strokeWidth="1.5" strokeLinecap="round" />
            </g>
          )}
        </svg>
      </div>

      {/* Anchored Bottom Category Label Pill */}
      <div className="w-full z-10 mt-auto">
        <span
          className={`block w-full truncate rounded-lg ${theme.badgeBg} py-0.5 px-1.5 text-center text-[9px] sm:text-[10px] font-bold uppercase tracking-wider shadow-2xs`}
        >
          {theme.categoryLabel}
        </span>
      </div>
    </div>
  );
};

// ============================================================================
// 2. USER & PROFILE AVATAR
// Illustrated persona avatar for students, alumni, mentors and faculty.
// ============================================================================

export interface UserAvatarProps {
  name: string;
  role?: string | null | undefined;
  size?: "xs" | "sm" | "md" | "lg" | "xl" | undefined;
  className?: string | undefined;
  showBadge?: boolean | undefined;
  src?: string | null | undefined;
}

export const UserAvatar: React.FC<UserAvatarProps> = ({
  name,
  role = "member",
  size = "md",
  className = "",
  showBadge = false,
  src = null,
}) => {
  const [imgError, setImgError] = React.useState(false);
  const cleanName = (name || "Member").trim();
  const seed = getHash(cleanName);
  const normRole = (role || "member").toLowerCase();
  const badgeColor = normRole.includes("alum")
    ? "bg-purple-500"
    : normRole.includes("faculty") || normRole.includes("mentor")
    ? "bg-emerald-500"
    : "bg-teal-500";

  // Palette combinations for user avatars
  const palettes = [
    { bg: "from-teal-500 to-emerald-600", text: "text-white", border: "border-teal-200" },
    { bg: "from-indigo-500 to-purple-600", text: "text-white", border: "border-indigo-200" },
    { bg: "from-sky-500 to-blue-600", text: "text-white", border: "border-sky-200" },
    { bg: "from-amber-500 to-orange-600", text: "text-white", border: "border-amber-200" },
    { bg: "from-rose-500 to-pink-600", text: "text-white", border: "border-rose-200" },
    { bg: "from-violet-500 to-fuchsia-600", text: "text-white", border: "border-violet-200" },
  ];
  const palette = palettes[seed % palettes.length] ?? palettes[0]!;

  // Size specifications
  const sizeClasses = {
    xs: "h-6 w-6 text-[10px]",
    sm: "h-8 w-8 text-xs",
    md: "h-10 w-10 text-sm",
    lg: "h-12 w-12 sm:h-14 sm:w-14 text-base",
    xl: "h-16 w-16 text-lg",
  };

  // Avatar persona style variant (0 to 5)
  const personaVariant = seed % 6;

  if (src && !imgError) {
    return (
      <div
        className={`relative inline-flex shrink-0 items-center justify-center rounded-full border-2 ${palette.border} bg-slate-100 shadow-2xs overflow-hidden ${sizeClasses[size]} ${className}`}
        title={`${cleanName} (${role || "Member"})`}
      >
        <img
          src={src}
          alt={cleanName}
          className="h-full w-full object-cover"
          onError={() => setImgError(true)}
          loading="lazy"
        />
        {showBadge && (
          <span
            className={`absolute bottom-0 right-0 block h-2.5 w-2.5 rounded-full ring-2 ring-white ${badgeColor}`}
          />
        )}
      </div>
    );
  }

  return (
    <div
      className={`relative inline-flex shrink-0 items-center justify-center rounded-full border-2 ${palette.border} bg-gradient-to-tr ${palette.bg} shadow-2xs overflow-hidden ${sizeClasses[size]} ${className}`}
      title={`${cleanName} (${role || "Member"})`}
    >
      <svg
        viewBox="0 0 40 40"
        className="h-full w-full"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id={`u-skin-${seed}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#FED7AA" />
            <stop offset="100%" stopColor="#FDBA74" />
          </linearGradient>
        </defs>

        {/* Persona Background Glow */}
        <circle cx="20" cy="20" r="19" fill="currentColor" fillOpacity="0.1" />

        {/* Persona 0: Student with modern beanie */}
        {personaVariant === 0 && (
          <g>
            <path d="M8 38C8 28 14 25 20 25C26 25 32 28 32 38" fill="#FFF" fillOpacity="0.9" />
            <rect x="18" y="21" width="4" height="6" fill={`url(#u-skin-${seed})`} />
            <circle cx="20" cy="15" r="7.5" fill={`url(#u-skin-${seed})`} />
            <path d="M12 14C12 9 15 6 20 6C25 6 28 9 28 14Z" fill="#1E1B4B" />
            <rect x="12" y="12" width="16" height="3" rx="1.5" fill="#4338CA" />
            <circle cx="17.5" cy="15" r="1" fill="#1E293B" />
            <circle cx="22.5" cy="15" r="1" fill="#1E293B" />
            <path d="M18.5 18C19.2 19 20.8 19 21.5 18" stroke="#7C2D12" strokeWidth="1" strokeLinecap="round" />
          </g>
        )}

        {/* Persona 1: Engineer with glasses */}
        {personaVariant === 1 && (
          <g>
            <path d="M8 38C8 28 14 25 20 25C26 25 32 28 32 38" fill="#FFF" fillOpacity="0.9" />
            <path d="M18 25L20 29L22 25" fill="#0D9488" />
            <rect x="18" y="21" width="4" height="6" fill={`url(#u-skin-${seed})`} />
            <circle cx="20" cy="15" r="7.5" fill={`url(#u-skin-${seed})`} />
            <path d="M12 13C12 8 16 6 20 6C24 6 28 8 28 13C26 10 22 10 20 10C18 10 14 10 12 13Z" fill="#3B0764" />
            <rect x="15" y="13.5" width="4" height="3" rx="1" stroke="#0F172A" strokeWidth="1" fill="#FFF" fillOpacity="0.4" />
            <rect x="21" y="13.5" width="4" height="3" rx="1" stroke="#0F172A" strokeWidth="1" fill="#FFF" fillOpacity="0.4" />
            <line x1="19" y1="15" x2="21" y2="15" stroke="#0F172A" strokeWidth="1" />
            <path d="M18.5 18.5C19.2 19.5 20.8 19.5 21.5 18.5" stroke="#7C2D12" strokeWidth="1" strokeLinecap="round" />
          </g>
        )}

        {/* Persona 2: Designer with curly hair */}
        {personaVariant === 2 && (
          <g>
            <path d="M8 38C8 28 14 25 20 25C26 25 32 28 32 38" fill="#FFF" fillOpacity="0.9" />
            <circle cx="13" cy="12" r="3" fill="#1C1917" />
            <circle cx="27" cy="12" r="3" fill="#1C1917" />
            <circle cx="20" cy="8" r="3.5" fill="#1C1917" />
            <rect x="18" y="21" width="4" height="6" fill={`url(#u-skin-${seed})`} />
            <circle cx="20" cy="15" r="7.5" fill={`url(#u-skin-${seed})`} />
            <path d="M13 13C13 8 16 7 20 7C24 7 27 8 27 13Z" fill="#1C1917" />
            <circle cx="17.5" cy="15" r="1" fill="#1E293B" />
            <circle cx="22.5" cy="15" r="1" fill="#1E293B" />
            <path d="M18.5 18C19.2 19.5 20.8 19.5 21.5 18" stroke="#7C2D12" strokeWidth="1" strokeLinecap="round" />
          </g>
        )}

        {/* Persona 3: Mentor with smart blazer */}
        {personaVariant === 3 && (
          <g>
            <path d="M8 38C8 28 14 25 20 25C26 25 32 28 32 38" fill="#1E293B" />
            <path d="M17 25L20 31L23 25" fill="#FFF" />
            <rect x="18" y="21" width="4" height="6" fill={`url(#u-skin-${seed})`} />
            <circle cx="20" cy="15" r="7.5" fill={`url(#u-skin-${seed})`} />
            <path d="M13 12C13 8 16 6 20 6C24 6 27 8 27 12C25 10 21 10 20 10C19 10 15 10 13 12Z" fill="#451A03" />
            <circle cx="17.5" cy="15" r="1" fill="#1E293B" />
            <circle cx="22.5" cy="15" r="1" fill="#1E293B" />
            <path d="M18 18.5C19 19.5 21 19.5 22 18.5" stroke="#7C2D12" strokeWidth="1" strokeLinecap="round" />
          </g>
        )}

        {/* Persona 4: Creative researcher with bun */}
        {personaVariant === 4 && (
          <g>
            <circle cx="20" cy="6" r="3" fill="#713F12" />
            <path d="M8 38C8 28 14 25 20 25C26 25 32 28 32 38" fill="#FFF" fillOpacity="0.9" />
            <rect x="18" y="21" width="4" height="6" fill={`url(#u-skin-${seed})`} />
            <circle cx="20" cy="15" r="7.5" fill={`url(#u-skin-${seed})`} />
            <path d="M13 13C13 8 16 7 20 7C24 7 27 8 27 13C25 11 21 11 20 11C19 11 15 11 13 13Z" fill="#713F12" />
            <circle cx="17.5" cy="15" r="1" fill="#1E293B" />
            <circle cx="22.5" cy="15" r="1" fill="#1E293B" />
            <path d="M18.5 18C19.2 19.2 20.8 19.2 21.5 18" stroke="#7C2D12" strokeWidth="1" strokeLinecap="round" />
          </g>
        )}

        {/* Persona 5: Tech lead with headphones */}
        {personaVariant === 5 && (
          <g>
            <path d="M8 38C8 28 14 25 20 25C26 25 32 28 32 38" fill="#FFF" fillOpacity="0.9" />
            <rect x="18" y="21" width="4" height="6" fill={`url(#u-skin-${seed})`} />
            <circle cx="20" cy="15" r="7.5" fill={`url(#u-skin-${seed})`} />
            <path d="M13 12C13 8 16 6 20 6C24 6 27 8 27 12Z" fill="#172554" />
            {/* Headphones arc & pads */}
            <path d="M12 16C12 10 15 8 20 8C25 8 28 10 28 16" stroke="#0F172A" strokeWidth="2" strokeLinecap="round" />
            <rect x="11" y="14" width="3" height="5" rx="1.5" fill="#0284C7" />
            <rect x="26" y="14" width="3" height="5" rx="1.5" fill="#0284C7" />
            <circle cx="17.5" cy="15" r="1" fill="#1E293B" />
            <circle cx="22.5" cy="15" r="1" fill="#1E293B" />
            <path d="M18.5 18.5C19.2 19.5 20.8 19.5 21.5 18.5" stroke="#7C2D12" strokeWidth="1" strokeLinecap="round" />
          </g>
        )}
      </svg>

      {/* Role badge indicator dot */}
      {showBadge && (
        <span
          className={`absolute bottom-0 right-0 block h-2.5 w-2.5 rounded-full border border-white ${
            normRole.includes("alum")
              ? "bg-purple-500"
              : normRole.includes("faculty") || normRole.includes("mentor")
              ? "bg-emerald-500"
              : "bg-teal-500"
          }`}
          title={role || "Active Member"}
        />
      )}
    </div>
  );
};
