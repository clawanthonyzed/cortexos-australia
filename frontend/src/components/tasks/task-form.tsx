"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
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
import { useCreateTask } from "@/hooks/use-tasks";
import { toast } from "sonner";
import { mutate } from "swr";

const schema = z.object({
  title: z.string().min(1, "Title is required").max(200),
  description: z.string().max(2000).optional().default(""),
  priority: z.enum(["low", "normal", "high", "critical"]),
  agentId: z.string().optional(),
  venture: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

interface TaskFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function TaskForm({ onSuccess, onCancel }: TaskFormProps) {
  const { trigger: createTask, isMutating } = useCreateTask();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: "",
      description: "",
      priority: "normal",
      agentId: "",
      venture: "",
    },
  });

  const priority = watch("priority");

  const onSubmit = async (data: FormValues) => {
    try {
      await createTask({
        title: data.title,
        description: data.description ?? "",
        priority: data.priority,
        agentId: data.agentId || null,
        workflowId: null,
        venture: data.venture || null,
        tags: [],
        input: {},
      });
      await mutate((key: string) => key.startsWith("/tasks"));
      toast.success("Task created and queued");
      onSuccess?.();
    } catch {
      toast.error("Failed to create task");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="title">Task Title</Label>
        <Input
          id="title"
          placeholder="What should be done?"
          {...register("title")}
        />
        {errors.title && <p className="text-xs text-cortex-error">{errors.title.message}</p>}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          placeholder="Detailed instructions, context, expected output..."
          rows={4}
          {...register("description")}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="priority">Priority</Label>
          <Select value={priority} onValueChange={(v) => setValue("priority", v as FormValues["priority"])}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="normal">Normal</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="agentId">Assign to Agent</Label>
          <Input
            id="agentId"
            placeholder="Agent ID (optional)"
            {...register("agentId")}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="venture">Venture</Label>
        <Input
          id="venture"
          placeholder="e.g. bloom-bub (optional)"
          {...register("venture")}
        />
      </div>

      <div className="flex justify-end gap-2 pt-2">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={isMutating}>
          {isMutating ? "Creating..." : "Create Task"}
        </Button>
      </div>
    </form>
  );
}
