"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import type { Agent } from "@/types/agent";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateAgent, useUpdateAgent } from "@/hooks/use-agents";
import { toast } from "sonner";
import { mutate } from "swr";

const MODELS = [
  "claude-sonnet-4-6",
  "claude-opus-4",
  "claude-haiku-3-5",
  "gpt-4o",
  "gpt-4o-mini",
  "gemini-1.5-pro",
  "gemini-1.5-flash",
];

const schema = z.object({
  name: z.string().min(1, "Name is required").max(80),
  purpose: z.string().min(1, "Purpose is required").max(120),
  description: z.string().max(1000).optional().default(""),
  model: z.string().min(1, "Model is required"),
  venture: z.string().optional().nullable(),
  tags: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

interface AgentFormProps {
  agent?: Agent;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function AgentForm({ agent, onSuccess, onCancel }: AgentFormProps) {
  const isEditing = !!agent;
  const { trigger: createAgent, isMutating: creating } = useCreateAgent();
  const { trigger: updateAgent, isMutating: updating } = useUpdateAgent(agent?.id ?? "");

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: agent?.name ?? "",
      purpose: agent?.purpose ?? "",
      description: agent?.description ?? "",
      model: agent?.model ?? "claude-sonnet-4-6",
      venture: agent?.venture ?? "",
      tags: agent?.tags?.join(", ") ?? "",
    },
  });

  const selectedModel = watch("model");

  const onSubmit = async (data: FormValues) => {
    const payload = {
      ...data,
      description: data.description ?? "",
      tags: data.tags ? data.tags.split(",").map((t) => t.trim()).filter(Boolean) : [],
      venture: data.venture || null,
      capabilities: [] as Agent["capabilities"],
      config: {},
    };

    try {
      if (isEditing) {
        await updateAgent(payload);
        toast.success("Agent updated");
      } else {
        await createAgent(payload);
        toast.success("Agent created");
      }
      await mutate("/agents");
      onSuccess?.();
    } catch {
      toast.error(isEditing ? "Failed to update agent" : "Failed to create agent");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2 space-y-1.5">
          <Label htmlFor="name">Name</Label>
          <Input
            id="name"
            placeholder="e.g. Content Writer"
            {...register("name")}
          />
          {errors.name && <p className="text-xs text-cortex-error">{errors.name.message}</p>}
        </div>

        <div className="col-span-2 space-y-1.5">
          <Label htmlFor="purpose">Purpose</Label>
          <Input
            id="purpose"
            placeholder="One-line description of what this agent does"
            {...register("purpose")}
          />
          {errors.purpose && <p className="text-xs text-cortex-error">{errors.purpose.message}</p>}
        </div>

        <div className="col-span-2 space-y-1.5">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            placeholder="Detailed description, capabilities, constraints..."
            rows={3}
            {...register("description")}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="model">Model</Label>
          <Select
            value={selectedModel}
            onValueChange={(v) => setValue("model", v)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MODELS.map((m) => (
                <SelectItem key={m} value={m}>{m}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="venture">Venture</Label>
          <Input
            id="venture"
            placeholder="e.g. bloom-bub (optional)"
            {...register("venture")}
          />
        </div>

        <div className="col-span-2 space-y-1.5">
          <Label htmlFor="tags">Tags</Label>
          <Input
            id="tags"
            placeholder="content, seo, email (comma-separated)"
            {...register("tags")}
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={creating || updating}>
          {creating || updating ? "Saving..." : isEditing ? "Update Agent" : "Create Agent"}
        </Button>
      </div>
    </form>
  );
}
