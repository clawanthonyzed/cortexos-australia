"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import type { Product } from "@/types/product";
import api from "@/lib/api";

const productSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(200),
  description: z.string().min(10, "Description must be at least 10 characters"),
  product_type: z.enum([
    "digital_download",
    "course",
    "template",
    "prompt_pack",
    "ebook",
    "automation",
    "ai_asset",
    "other",
  ]),
  price_aud: z.coerce.number().min(0).max(10000),
  tags: z.string().optional(),
  gumroad_enabled: z.boolean().optional(),
  etsy_enabled: z.boolean().optional(),
  lemonsqueezy_enabled: z.boolean().optional(),
});

type ProductFormValues = z.infer<typeof productSchema>;

interface ProductFormProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (product: Product) => void;
  existing?: Product;
}

export function ProductForm({ open, onClose, onSuccess, existing }: ProductFormProps) {
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
    reset,
  } = useForm<ProductFormValues>({
    resolver: zodResolver(productSchema),
    defaultValues: existing
      ? {
          name: existing.name,
          description: existing.description,
          product_type: existing.product_type,
          price_aud: existing.price_aud,
          tags: existing.tags?.join(", ") ?? "",
        }
      : {
          product_type: "digital_download",
          price_aud: 0,
        },
  });

  const onSubmit = async (values: ProductFormValues) => {
    setLoading(true);
    try {
      const payload = {
        ...values,
        tags: values.tags
          ? values.tags.split(",").map((t) => t.trim()).filter(Boolean)
          : [],
      };
      const response = existing
        ? await api.patch(`/api/v1/products/${existing.id}`, payload)
        : await api.post("/api/v1/products/", payload);
      onSuccess(response.data);
      reset();
      onClose();
    } catch (err) {
      console.error("Failed to save product", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="bg-cortex-surface border-cortex-border text-cortex-text max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-cortex-text">
            {existing ? "Edit Product" : "New Product"}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Name */}
          <div className="space-y-1.5">
            <Label className="text-sm text-cortex-text">Product Name</Label>
            <Input
              {...register("name")}
              placeholder="e.g. AI Prompt Pack — Social Media"
              className="bg-cortex-bg border-cortex-border"
            />
            {errors.name && (
              <p className="text-xs text-red-400">{errors.name.message}</p>
            )}
          </div>

          {/* Type + Price */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label className="text-sm text-cortex-text">Type</Label>
              <Select
                defaultValue={existing?.product_type ?? "digital_download"}
                onValueChange={(v) => setValue("product_type", v as ProductFormValues["product_type"])}
              >
                <SelectTrigger className="bg-cortex-bg border-cortex-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-cortex-surface border-cortex-border">
                  <SelectItem value="digital_download">Digital Download</SelectItem>
                  <SelectItem value="course">Course</SelectItem>
                  <SelectItem value="template">Template</SelectItem>
                  <SelectItem value="prompt_pack">Prompt Pack</SelectItem>
                  <SelectItem value="ebook">eBook</SelectItem>
                  <SelectItem value="automation">Automation</SelectItem>
                  <SelectItem value="ai_asset">AI Asset</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm text-cortex-text">Price (AUD)</Label>
              <Input
                {...register("price_aud")}
                type="number"
                step="0.01"
                min={0}
                placeholder="0.00"
                className="bg-cortex-bg border-cortex-border"
              />
              {errors.price_aud && (
                <p className="text-xs text-red-400">{errors.price_aud.message}</p>
              )}
            </div>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <Label className="text-sm text-cortex-text">Description</Label>
            <Textarea
              {...register("description")}
              placeholder="Describe what this product does and who it's for..."
              className="bg-cortex-bg border-cortex-border resize-none"
              rows={4}
            />
            {errors.description && (
              <p className="text-xs text-red-400">{errors.description.message}</p>
            )}
          </div>

          {/* Tags */}
          <div className="space-y-1.5">
            <Label className="text-sm text-cortex-text">Tags</Label>
            <Input
              {...register("tags")}
              placeholder="ai, templates, social-media (comma-separated)"
              className="bg-cortex-bg border-cortex-border"
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="border-cortex-border"
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Saving...
                </>
              ) : existing ? (
                "Update Product"
              ) : (
                "Create Product"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
