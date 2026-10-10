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
import { MemoryItem, type MemoryItemBackend } from "./memory-item";
import { fetcher } from "@/lib/api";
import { PageLoader } from "@/components/ui/loading-spinner";
import { EmptyState } from "@/components/ui/empty-state";
import { Brain } from "lucide-react";

interface MemoryListResponse {
  items: MemoryItemBackend[];
  total: number;
}

export function MemorySearch() {
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [submitted, setSubmitted] = useState("");

  const params = new URLSearchParams();
  if (typeFilter !== "all") params.set("memory_type", typeFilter);
  if (categoryFilter !== "all") params.set("category", categoryFilter);
  if (submitted) params.set("search", submitted);
  params.set("page_size", "100");
  const listKey = `/memory?${params.toString()}`;

  const { data: listData, isLoading } = useSWR<MemoryListResponse>(listKey, fetcher);

  const items: MemoryItemBackend[] = listData?.items ?? [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(query);
  };

  const handleClear = () => {
    setQuery("");
    setSubmitted("");
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSearch} className="flex gap-2 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-cortex-muted" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search memory by content, summary, or category..."
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
            <SelectItem value="long_term">Long-term</SelectItem>
          </SelectContent>
        </Select>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All categories</SelectItem>
            <SelectItem value="empire">Empire</SelectItem>
            <SelectItem value="ventures">Ventures</SelectItem>
            <SelectItem value="agents">Agents</SelectItem>
            <SelectItem value="workflows">Workflows</SelectItem>
            <SelectItem value="financial">Financial</SelectItem>
            <SelectItem value="feedback">Feedback</SelectItem>
            <SelectItem value="knowledge-graph">Knowledge Graph</SelectItem>
            <SelectItem value="interviews">Interviews</SelectItem>
          </SelectContent>
        </Select>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? "Searching..." : "Search"}
        </Button>
        {submitted && (
          <Button type="button" variant="outline" onClick={handleClear}>
            Clear
          </Button>
        )}
      </form>

      {isLoading ? (
        <PageLoader label="Loading memory..." />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Brain}
          title="No memory entries found"
          description={submitted ? `No results for "${submitted}"` : "Memory is empty"}
        />
      ) : (
        <div className="space-y-2">
          <p className="text-xs text-cortex-muted">
            {listData?.total ?? items.length} entr{(listData?.total ?? items.length) !== 1 ? "ies" : "y"}
            {submitted ? ` matching "${submitted}"` : ""}
            {categoryFilter !== "all" ? ` in ${categoryFilter}` : ""}
            {" — showing first 100"}
          </p>
          {items.map((item) => (
            <MemoryItem key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
