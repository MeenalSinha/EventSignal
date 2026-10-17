import type { EvidenceStatus } from "../types/opportunity";

interface Props {
  status: EvidenceStatus;
}

export function EvidenceBadge({ status }: Props) {
  switch (status) {
    case "found":
      return (
        <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
          Found in source
        </span>
      );
    case "multi_source":
      return (
        <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/20">
          Multi-source
        </span>
      );
    case "needs_verification":
      return (
        <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800 ring-1 ring-inset ring-amber-600/20">
          Needs verification
        </span>
      );
    case "not_found":
      return (
        <span className="inline-flex items-center rounded-full bg-gray-50 px-2 py-0.5 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/20">
          Not found
        </span>
      );
    case "sources_disagree":
      return (
        <span className="inline-flex items-center rounded-full bg-orange-50 px-2 py-0.5 text-xs font-medium text-orange-800 ring-1 ring-inset ring-orange-600/20">
          Sources disagree
        </span>
      );
    case "extraction_failed":
      return (
        <span className="inline-flex items-center rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">
          Extraction failed
        </span>
      );
    case "not_assessed":
    default:
      return (
        <span className="inline-flex items-center rounded-full bg-gray-50 px-2 py-0.5 text-xs font-medium text-gray-500 ring-1 ring-inset ring-gray-500/10">
          Not assessed
        </span>
      );
  }
}
