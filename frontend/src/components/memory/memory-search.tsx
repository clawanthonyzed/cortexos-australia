"use client";

import { useState } from "react";
import useSWR from "swr";
import { Search, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MemoryItem as MemoryItemComponent } from "./memory-item";
import { fetcher } from "@/lib/api";
import type { MemoryItem, MemorySearchResult } from "@/types/memory";
import { PageLoader } from "@/components/ui/loading-spinner";
import { EmptyState } from "@/components/ui/empty-state";
import { Brain } from "lucide-react";

export function MemorySearch() {
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [submitted, setSubmitted] = useState("");

  const searchKey = submitted
    ? `/memory/search?q=${encodeURIComponent(submitted)}&type=${typeFilter !== "all" ? typeFilter : ""}`
    : null;

  const listKey = `/memory?type=${typeFilter !== "all" ? typeFilter : ""}&limit=50`;

  const { data: searchResults, isLoading: searching } = useSWR<MemorySearchResult[]>(
    searchKey,
    fetcher
  );
  const { data: listData, isLoading: listing } = useSWR<{ items: MemoryItem[]; total: number }>(
    !searchKey ? listKey : null,
    fetcher
  );

  const isLoading = searching || listing;
  const items = searchResults
    ? searchResults.map((r) => r.item)
    : listData?.items ?? [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(query);
  };

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-cortex-muted" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search memory by key, value, or semantic meaning..."
            className="pl-9"
          />
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-36">
            <Filter className="h-3.5 w-3.5 mr-1 text-cortex-muted" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            <SelectItem value="episodic">Episodic</SelectItem>
            <SelectItem value="semantic">Semantic</SelectItem>
            <SelectItem value="procedural">Procedural</SelectItem>
            <SelectItem value="working">Working</SelectItem>
          </SelectContent>
        </Select>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? "Searching..." : "Search"}
        </Button>
      </form>

      {/* Results */}
      {isLoading ? (
        <PageLoader label="Searching memory..." />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Brain}
          title="No memory entries found"
          description={submitted ? `No results for "${submitted}"` : "Memory is empty"}
        />
      ) : (
        <div className="space-y-2">
          {submitted && (
            <p className="text-xs text-cortex-muted">
              {items.length} result{items.length !== 1 ? "s" : ""} for &ldquo;{submitted}&rdquo;
            </p>
          )}
          {items.map((item) => (
            <MemoryItemComponent key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
