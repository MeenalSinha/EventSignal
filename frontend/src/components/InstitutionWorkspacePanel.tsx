import React, { useEffect, useState } from "react";
import type { UserProfile } from "../types/auth";
import type {
  CampusAssignment,
  CampusPosition,
  Institution,
  Membership,
  OrganizationalUnit,
  WorkspaceSummary,
} from "../types/institution";
import {
  createCampusPosition,
  createInstitution,
  createOrganizationalUnit,
  fetchInstitution,
  fetchInstitutions,
  fetchWorkspaceAssignments,
  fetchWorkspaceMembers,
  fetchWorkspacePositions,
  fetchWorkspaceSummary,
  fetchWorkspaceUnits,
  joinWorkspace,
} from "../services/institutionService";
import { fetchDemoStatus } from "../services/authService";

interface InstitutionWorkspacePanelProps {
  currentUser: UserProfile | null;
  onOpenAuth: () => void;
}

export function InstitutionWorkspacePanel({
  currentUser,
  onOpenAuth,
}: InstitutionWorkspacePanelProps) {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [selectedInstId, setSelectedInstId] = useState<string | null>(null);
  const [summary, setSummary] = useState<WorkspaceSummary | null>(null);
  const [activeTab, setActiveTab] = useState<"positions" | "units" | "members">("positions");

  const [positions, setPositions] = useState<CampusPosition[]>([]);
  const [assignments, setAssignments] = useState<CampusAssignment[]>([]);
  const [units, setUnits] = useState<OrganizationalUnit[]>([]);
  const [members, setMembers] = useState<Membership[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Modals & forms
  const [showCreateInst, setShowCreateInst] = useState(false);
  const [instName, setInstName] = useState("");
  const [instSlug, setInstSlug] = useState("");
  const [instDomain, setInstDomain] = useState("");
  const [instLocation, setInstLocation] = useState("");
  const [instDescription, setInstDescription] = useState("");

  const [showAddUnit, setShowAddUnit] = useState(false);
  const [unitName, setUnitName] = useState("");
  const [unitCode, setUnitCode] = useState("");
  const [unitType, setUnitType] = useState("department");

  const [showAddPosition, setShowAddPosition] = useState(false);
  const [posTitle, setPosTitle] = useState("");
  const [posDesc, setPosDesc] = useState("");
  const [posIsLeadership, setPosIsLeadership] = useState(false);

  const [refreshCount, setRefreshCount] = useState(0);

  const refreshWorkspace = () => {
    setRefreshCount((c) => c + 1);
  };

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    fetchInstitutions()
      .then(async (list) => {
        if (!isMounted) return;
        const instMap = new Map<string, Institution>();
        list.forEach((i) => instMap.set(i.id, i));

        // 1. If currentUser has memberships, ensure their institution is represented
        if (currentUser?.memberships?.length) {
          for (const m of currentUser.memberships) {
            if (!instMap.has(m.institution_id)) {
              try {
                const inst = await fetchInstitution(m.institution_id);
                if (inst) instMap.set(inst.id, inst);
              } catch {
                instMap.set(m.institution_id, {
                  id: m.institution_id,
                  name: m.institution_name || "College Workspace",
                  slug: m.institution_slug || m.institution_id.slice(0, 10),
                  domain: null,
                  description: null,
                  location: null,
                  contact_email: null,
                  website_url: null,
                  status: "active",
                  verification_status: "verified",
                  verified_at: null,
                  created_at: "",
                  updated_at: "",
                });
              }
            }
          }
        }

        // 2. If directory is empty, check demo status to allow inspecting the demo collegiate workspace
        if (instMap.size === 0) {
          try {
            const demoStatus = await fetchDemoStatus();
            if (demoStatus.demo_mode_enabled && demoStatus.demo_institution_id) {
              const demoInst = await fetchInstitution(demoStatus.demo_institution_id);
              if (demoInst) instMap.set(demoInst.id, demoInst);
            }
          } catch {
            // Ignore demo status fetch failure
          }
        }

        if (!isMounted) return;
        const finalList = Array.from(instMap.values());
        setInstitutions(finalList);

        if (finalList.length > 0) {
          const preferredId =
            currentUser?.memberships?.[0]?.institution_id ||
            finalList[0]?.id;
          setSelectedInstId((prev) => (prev && instMap.has(prev) ? prev : (preferredId ?? null)));
        } else {
          setSelectedInstId(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (isMounted && err instanceof Error) setError(err.message);
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [currentUser, refreshCount]);

  useEffect(() => {
    if (!selectedInstId) {
      setSummary(null);
      setPositions([]);
      setAssignments([]);
      setUnits([]);
      setMembers([]);
      setLoading(false);
      return;
    }
    let isMounted = true;
    setLoading(true);
    Promise.all([
      fetchWorkspaceSummary(selectedInstId),
      fetchWorkspacePositions(selectedInstId),
      fetchWorkspaceAssignments(selectedInstId),
      fetchWorkspaceUnits(selectedInstId),
      fetchWorkspaceMembers(selectedInstId).catch(() => []),
    ])
      .then(([sumData, posList, assignList, unitList, memberList]) => {
        if (!isMounted) return;
        setSummary(sumData);
        setPositions(posList);
        setAssignments(assignList);
        setUnits(unitList);
        setMembers(memberList);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (!isMounted) return;
        if (err instanceof Error) setError(err.message);
        setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedInstId, refreshCount]);

  const handleCreateInstitution = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) {
      onOpenAuth();
      return;
    }
    setError(null);
    try {
      const created = await createInstitution({
        name: instName,
        slug: instSlug,
        domain: instDomain || undefined,
        location: instLocation || undefined,
        description: instDescription || undefined,
      });
      setSuccessMsg(`College workspace "${created.name}" created!`);
      setShowCreateInst(false);
      setInstName("");
      setInstSlug("");
      setInstDomain("");
      setInstLocation("");
      setInstDescription("");
      setSelectedInstId(created.id);
      refreshWorkspace();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  const handleJoinWorkspace = async (role: string) => {
    if (!currentUser) {
      onOpenAuth();
      return;
    }
    if (!selectedInstId) return;
    try {
      await joinWorkspace(selectedInstId, role);
      setSuccessMsg(`Joined workspace as ${role}!`);
      refreshWorkspace();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  const handleAddUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInstId) return;
    try {
      await createOrganizationalUnit(selectedInstId, {
        name: unitName,
        code: unitCode || undefined,
        unit_type: unitType,
      });
      setShowAddUnit(false);
      setUnitName("");
      setUnitCode("");
      setSuccessMsg("Department / unit added!");
      refreshWorkspace();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  const handleAddPosition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInstId) return;
    try {
      await createCampusPosition(selectedInstId, {
        title: posTitle,
        description: posDesc || undefined,
        is_leadership: posIsLeadership,
      });
      setShowAddPosition(false);
      setPosTitle("");
      setPosDesc("");
      setPosIsLeadership(false);
      setSuccessMsg("Official campus position catalogued!");
      refreshWorkspace();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    }
  };

  const selectedInst = institutions.find((i) => i.id === selectedInstId);
  const isMemberOfSelected =
    currentUser &&
    currentUser.memberships.some((m) => m.institution_id === selectedInstId);

  return (
    <div className="space-y-8">
      {/* Top Bar: Selector & Register College button */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs font-semibold uppercase tracking-wider text-ink-soft">
            College Workspace:
          </label>
          <select
            value={selectedInstId || ""}
            onChange={(e) => setSelectedInstId(e.target.value)}
            disabled={institutions.length === 0}
            className="min-w-[280px] rounded-xl border border-line bg-paper px-3 py-2 text-sm font-semibold text-ink outline-none focus:border-accent disabled:bg-paper-warm disabled:text-ink-soft/60"
          >
            {institutions.length === 0 ? (
              <option value="" disabled>
                {loading ? "Loading workspaces..." : "No college workspaces found"}
              </option>
            ) : (
              institutions.map((inst) => (
                <option key={inst.id} value={inst.id}>
                  {inst.name} ({inst.slug})
                </option>
              ))
            )}
          </select>
          {loading && (
            <span className="text-xs font-medium text-ink-soft animate-pulse">
              Syncing...
            </span>
          )}
        </div>

        <button
          onClick={() => {
            if (!currentUser) {
              onOpenAuth();
            } else {
              setShowCreateInst(true);
            }
          }}
          className="inline-flex items-center justify-center rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-accent/90"
        >
          + Register College Workspace
        </button>
      </div>

      {/* Alert / Notification banners */}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}
      {successMsg && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
          {successMsg}
        </div>
      )}

      {/* Empty State Banner if no workspaces */}
      {institutions.length === 0 && !loading && (
        <div className="rounded-2xl border border-line bg-paper p-8 text-center shadow-sm">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-accent/10 text-accent mb-4">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <h3 className="font-display text-lg font-bold text-ink">No College Workspaces Available</h3>
          <p className="mt-2 text-sm text-ink-soft max-w-md mx-auto">
            {!currentUser
              ? "You are exploring in Guest Mode. Launch Demo Mode to explore the Apex Institute of Technology collegiate workspace, or register a new campus workspace."
              : "Register your college workspace above to initialize campus leadership roles, departments, and verified member directories."}
          </p>
          {!currentUser && (
            <div className="mt-6 flex justify-center gap-3">
              <button
                onClick={onOpenAuth}
                className="rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-accent/90"
              >
                Sign In / Launch Demo Mode
              </button>
            </div>
          )}
        </div>
      )}

      {/* Active College Header & Workspace Summary Card */}
      {selectedInst && (
        <div className="rounded-2xl border border-line bg-paper p-6 shadow-sm sm:p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2.5">
                <h2 className="font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
                  {selectedInst.name}
                </h2>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
                  <svg className="h-3 w-3 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  Verified Institutional Workspace
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-4 text-sm text-ink-soft">
                {selectedInst.location && (
                  <span className="inline-flex items-center gap-1">
                    <svg className="h-3.5 w-3.5 text-ink-soft shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {selectedInst.location}
                  </span>
                )}
                {selectedInst.domain && (
                  <span className="inline-flex items-center gap-1">
                    <svg className="h-3.5 w-3.5 text-ink-soft shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                    </svg>
                    {selectedInst.domain}
                  </span>
                )}
                {selectedInst.website_url && (
                  <a
                    href={selectedInst.website_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-accent hover:underline"
                  >
                    Visit Campus Site
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
              </div>

              {selectedInst.description && (
                <p className="mt-2 text-sm leading-relaxed text-ink-soft max-w-3xl">
                  {selectedInst.description}
                </p>
              )}
            </div>

            <div className="flex flex-col gap-2 shrink-0">
              {isMemberOfSelected ? (
                <span className="rounded-xl bg-paper-warm px-4 py-2 text-center text-xs font-bold uppercase tracking-wider text-emerald-700 border border-emerald-200">
                  Affiliated Member
                </span>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleJoinWorkspace("student")}
                    className="rounded-xl bg-ink px-3 py-2 text-xs font-semibold text-paper hover:bg-ink-light"
                  >
                    Join as Student
                  </button>
                  <button
                    onClick={() => handleJoinWorkspace("alumni")}
                    className="rounded-xl border border-line bg-paper px-3 py-2 text-xs font-semibold text-ink hover:bg-paper-warm"
                  >
                    Join as Alum
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Metrics Overview Grid */}
          {summary && (
            <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4 pt-6 border-t border-line">
              <div className="rounded-xl bg-paper-warm p-4">
                <div className="text-2xl font-bold text-ink">{summary.total_members}</div>
                <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft mt-1">
                  Active Members
                </div>
              </div>
              <div className="rounded-xl bg-paper-warm p-4">
                <div className="text-2xl font-bold text-ink">{summary.total_units}</div>
                <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft mt-1">
                  Units & Departments
                </div>
              </div>
              <div className="rounded-xl bg-paper-warm p-4">
                <div className="text-2xl font-bold text-ink">{summary.total_positions}</div>
                <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft mt-1">
                  Campus Positions
                </div>
              </div>
              <div className="rounded-xl bg-paper-warm p-4">
                <div className="text-2xl font-bold text-ink">{summary.active_assignments}</div>
                <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft mt-1">
                  Verified Appointments
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tabs navigation */}
      {selectedInst && (
        <>
          <div className="border-b border-line">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab("positions")}
            className={`pb-4 text-sm font-semibold border-b-2 transition ${
              activeTab === "positions"
                ? "border-accent text-accent"
                : "border-transparent text-ink-soft hover:text-ink"
            }`}
          >
            Campus Leadership & Positions ({positions.length})
          </button>
          <button
            onClick={() => setActiveTab("units")}
            className={`pb-4 text-sm font-semibold border-b-2 transition ${
              activeTab === "units"
                ? "border-accent text-accent"
                : "border-transparent text-ink-soft hover:text-ink"
            }`}
          >
            Departments & Units ({units.length})
          </button>
          <button
            onClick={() => setActiveTab("members")}
            className={`pb-4 text-sm font-semibold border-b-2 transition ${
              activeTab === "members"
                ? "border-accent text-accent"
                : "border-transparent text-ink-soft hover:text-ink"
            }`}
          >
            Members & Community ({members.length})
          </button>
        </nav>
      </div>

      {/* Tab 1: Campus Leadership & Positions */}
      {activeTab === "positions" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-display text-lg font-bold">Official Campus Roles</h3>
              <p className="text-xs text-ink-soft">
                Verified positions distinguishing official authority from self-reported claims.
              </p>
            </div>
            <button
              onClick={() => setShowAddPosition(true)}
              className="rounded-xl border border-line bg-paper px-3 py-1.5 text-xs font-semibold text-ink hover:bg-paper-warm"
            >
              + Define Position
            </button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {positions.map((pos) => {
              const posAssignments = assignments.filter((a) => a.position_id === pos.id);
              return (
                <div
                  key={pos.id}
                  className="rounded-xl border border-line bg-paper p-5 shadow-sm space-y-3"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-ink">{pos.title}</h4>
                      {pos.description && (
                        <p className="text-xs text-ink-soft mt-1 leading-relaxed">
                          {pos.description}
                        </p>
                      )}
                    </div>
                    {pos.is_leadership && (
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-800 border border-amber-200">
                        Leadership
                      </span>
                    )}
                  </div>

                  <div className="pt-2 border-t border-line text-xs">
                    <span className="font-semibold text-ink-soft">Current Appointees: </span>
                    {posAssignments.length === 0 ? (
                      <span className="text-ink-soft italic">No active appointment</span>
                    ) : (
                      <div className="mt-1.5 space-y-1">
                        {posAssignments.map((a) => (
                          <div
                            key={a.id}
                            className="flex items-center justify-between rounded bg-paper-warm p-1.5"
                          >
                            <span className="font-medium text-ink">
                              {a.user_full_name || a.user_email || "Appointed Member"}
                            </span>
                            <span
                              className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                                a.verification_status === "verified"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : "bg-amber-100 text-amber-800"
                              }`}
                            >
                              {a.verification_status}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 2: Organizational Units */}
      {activeTab === "units" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-display text-lg font-bold">Campus Departments & Offices</h3>
              <p className="text-xs text-ink-soft">
                Configurable hierarchy for academic departments, placement cells, and alumni bodies.
              </p>
            </div>
            <button
              onClick={() => setShowAddUnit(true)}
              className="rounded-xl border border-line bg-paper px-3 py-1.5 text-xs font-semibold text-ink hover:bg-paper-warm"
            >
              + Add Department / Unit
            </button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {units.map((u) => (
              <div
                key={u.id}
                className="rounded-xl border border-line bg-paper p-5 shadow-sm space-y-2"
              >
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-ink">{u.name}</h4>
                  {u.code && (
                    <span className="rounded bg-paper-warm px-2 py-0.5 text-xs font-bold text-ink-soft">
                      {u.code}
                    </span>
                  )}
                </div>
                <div className="text-xs font-medium capitalize text-accent">
                  Type: {u.unit_type.replace("_", " ")}
                </div>
                {u.description && (
                  <p className="text-xs text-ink-soft leading-relaxed">{u.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Members & Community */}
      {activeTab === "members" && (
        <div className="space-y-6">
          <div>
            <h3 className="font-display text-lg font-bold">Authorized Members</h3>
            <p className="text-xs text-ink-soft">
              Verified campus directory with role-based access control and tenant isolation.
            </p>
          </div>

          <div className="overflow-x-auto rounded-xl border border-line bg-paper">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-line bg-paper-warm text-xs font-semibold uppercase tracking-wider text-ink-soft">
                <tr>
                  <th className="px-4 py-3">Member Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Campus Role</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {members.map((m) => (
                  <tr key={m.id} className="hover:bg-paper-warm/50">
                    <td className="px-4 py-3 font-semibold text-ink">
                      {m.user_full_name || "Community Member"}
                    </td>
                    <td className="px-4 py-3 text-ink-soft">{m.user_email || "—"}</td>
                    <td className="px-4 py-3">
                      <span className="rounded-full bg-paper-warm px-2.5 py-0.5 text-xs font-semibold capitalize text-ink">
                        {m.role.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                        {m.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-ink-soft">
                      {new Date(m.joined_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
        </>
      )}

      {/* Modal: Register New College */}
      {showCreateInst && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-line bg-paper p-6 shadow-2xl sm:p-8">
            <div className="flex items-center justify-between border-b border-line pb-4">
              <h3 className="font-display text-xl font-bold">Register College Workspace</h3>
              <button
                onClick={() => setShowCreateInst(false)}
                aria-label="Close"
                className="rounded-lg p-1 text-ink-soft hover:bg-paper-warm"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleCreateInstitution} className="mt-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  College / Institution Full Name *
                </label>
                <input
                  type="text"
                  required
                  value={instName}
                  onChange={(e) => setInstName(e.target.value)}
                  placeholder="e.g. Indraprastha Institute of Information Technology Delhi"
                  className="mt-1 w-full rounded-xl border border-line bg-paper px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                    Workspace Slug (lowercase) *
                  </label>
                  <input
                    type="text"
                    required
                    pattern="^[a-z0-9-]+$"
                    value={instSlug}
                    onChange={(e) => setInstSlug(e.target.value.toLowerCase())}
                    placeholder="e.g. iiitd"
                    className="mt-1 w-full rounded-xl border border-line bg-paper px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                    Academic Domain
                  </label>
                  <input
                    type="text"
                    value={instDomain}
                    onChange={(e) => setInstDomain(e.target.value)}
                    placeholder="e.g. iiitd.ac.in"
                    className="mt-1 w-full rounded-xl border border-line bg-paper px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  Campus Location
                </label>
                <input
                  type="text"
                  value={instLocation}
                  onChange={(e) => setInstLocation(e.target.value)}
                  placeholder="City, State, Country"
                  className="mt-1 w-full rounded-xl border border-line bg-paper px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  Institutional Mission / Overview
                </label>
                <textarea
                  value={instDescription}
                  onChange={(e) => setInstDescription(e.target.value)}
                  rows={3}
                  placeholder="Brief description of the university or college."
                  className="mt-1 w-full rounded-xl border border-line bg-paper px-3.5 py-2.5 text-sm text-ink outline-none focus:border-accent"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-line">
                <button
                  type="button"
                  onClick={() => setShowCreateInst(false)}
                  className="rounded-xl border border-line px-4 py-2 text-sm font-semibold text-ink hover:bg-paper-warm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-accent px-5 py-2 text-sm font-semibold text-white hover:bg-accent/90"
                >
                  Register Workspace
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Department / Unit */}
      {showAddUnit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-line bg-paper p-6 shadow-2xl">
            <h3 className="font-display text-lg font-bold border-b border-line pb-3">
              Add Organizational Unit
            </h3>
            <form onSubmit={handleAddUnit} className="mt-4 space-y-3">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  Department / Office Name *
                </label>
                <input
                  type="text"
                  required
                  value={unitName}
                  onChange={(e) => setUnitName(e.target.value)}
                  placeholder="e.g. Training & Placement Cell"
                  className="mt-1 w-full rounded-xl border border-line bg-paper p-2.5 text-sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                    Code / Abbreviation
                  </label>
                  <input
                    type="text"
                    value={unitCode}
                    onChange={(e) => setUnitCode(e.target.value)}
                    placeholder="e.g. TPO"
                    className="mt-1 w-full rounded-xl border border-line bg-paper p-2.5 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                    Unit Type
                  </label>
                  <select
                    value={unitType}
                    onChange={(e) => setUnitType(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-line bg-paper p-2.5 text-sm"
                  >
                    <option value="department">Academic Dept</option>
                    <option value="administrative_office">Admin Office</option>
                    <option value="placement_cell">Placement Cell</option>
                    <option value="alumni_office">Alumni Office</option>
                    <option value="student_society">Student Club/Society</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddUnit(false)}
                  className="rounded-xl border border-line px-3 py-1.5 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-ink px-4 py-1.5 text-xs font-semibold text-paper"
                >
                  Save Unit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Define Position */}
      {showAddPosition && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-line bg-paper p-6 shadow-2xl">
            <h3 className="font-display text-lg font-bold border-b border-line pb-3">
              Define Official Campus Position
            </h3>
            <form onSubmit={handleAddPosition} className="mt-4 space-y-3">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  Position Title *
                </label>
                <input
                  type="text"
                  required
                  value={posTitle}
                  onChange={(e) => setPosTitle(e.target.value)}
                  placeholder="e.g. Placement Coordinator"
                  className="mt-1 w-full rounded-xl border border-line bg-paper p-2.5 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  Role Scope / Mandate
                </label>
                <textarea
                  value={posDesc}
                  onChange={(e) => setPosDesc(e.target.value)}
                  rows={2}
                  placeholder="Official responsibilities of this appointed position."
                  className="mt-1 w-full rounded-xl border border-line bg-paper p-2.5 text-sm"
                />
              </div>
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="leadership_check"
                  checked={posIsLeadership}
                  onChange={(e) => setPosIsLeadership(e.target.checked)}
                  className="rounded border-line text-accent"
                />
                <label htmlFor="leadership_check" className="text-xs font-medium text-ink">
                  Designate as Official Leadership / Sign-off Position
                </label>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddPosition(false)}
                  className="rounded-xl border border-line px-3 py-1.5 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-ink px-4 py-1.5 text-xs font-semibold text-paper"
                >
                  Catalogue Position
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
