/**
 * WorkSpace Provisioning Modal
 * 
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 22.1
 */

'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/modal';
import { useProvisionWorkspace } from '@/hooks/use-workspaces';
import { formatCurrency, cn } from '@/lib/utils';
import { BundleType, OperatingSystem } from '@/types';

interface ProvisionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Bundle pricing (monthly estimates)
const BUNDLE_PRICING = {
  [BundleType.STANDARD]: 25,
  [BundleType.PERFORMANCE]: 75,
  [BundleType.POWER]: 150,
  [BundleType.POWERPRO]: 300,
  [BundleType.GRAPHICS_G4DN]: 200,
  [BundleType.GRAPHICSPRO_G4DN]: 400,
};

// Bundle specifications
const BUNDLE_SPECS: Record<BundleType, { cpu: string; memory: string; gpu?: string; description: string }> = {
  [BundleType.STANDARD]: { cpu: '2 vCPU', memory: '8 GB', description: 'Light development work' },
  [BundleType.PERFORMANCE]: { cpu: '8 vCPU', memory: '32 GB', description: 'Standard development' },
  [BundleType.POWER]: { cpu: '16 vCPU', memory: '64 GB', description: 'Heavy workloads' },
  [BundleType.POWERPRO]: { cpu: '32 vCPU', memory: '128 GB', description: 'Intensive computing' },
  [BundleType.GRAPHICS_G4DN]: { cpu: '16 vCPU', memory: '64 GB', gpu: 'NVIDIA T4', description: 'GPU workloads' },
  [BundleType.GRAPHICSPRO_G4DN]: { cpu: '64 vCPU', memory: '256 GB', gpu: 'NVIDIA T4', description: 'Pro GPU workloads' },
};

export function ProvisionModal({ isOpen, onClose }: ProvisionModalProps) {
  const [bundleType, setBundleType] = useState<BundleType>(BundleType.STANDARD);
  const [operatingSystem, setOperatingSystem] = useState<OperatingSystem>(OperatingSystem.LINUX);
  const [blueprintId, setBlueprintId] = useState<string>('');
  const [region, setRegion] = useState<string>('');

  const { mutate: provisionWorkspace, isPending, isSuccess, error } = useProvisionWorkspace();

  // Reset form on close
  useEffect(() => {
    if (!isOpen) {
      setBundleType(BundleType.STANDARD);
      setOperatingSystem(OperatingSystem.LINUX);
      setBlueprintId('');
      setRegion('');
    }
  }, [isOpen]);

  // Close on success
  useEffect(() => {
    if (isSuccess) {
      setTimeout(() => onClose(), 1500);
    }
  }, [isSuccess, onClose]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    provisionWorkspace({
      bundle_type: bundleType,
      operating_system: operatingSystem,
      blueprint_id: blueprintId || undefined,
      region: region || undefined,
    });
  };

  const estimatedCost = BUNDLE_PRICING[bundleType];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Provision New Workspace" size="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Bundle Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:uppercase mb-3">
            Bundle Type
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.values(BundleType).map((type) => {
              const bundleSpecs = BUNDLE_SPECS[type];
              const isSelected = bundleType === type;
              
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => setBundleType(type)}
                  className={cn(
                    'p-4 border-2 rounded-lg text-left transition-all',
                    isSelected
                      ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20 retro:border-green-500 retro:bg-green-950'
                      : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 retro:border-green-700 retro:hover:border-green-500',
                    'retro:rounded-none'
                  )}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="font-semibold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                      {type}
                    </div>
                    <div className="text-sm font-medium text-blue-600 dark:text-blue-400 retro:text-green-400 retro:font-mono">
                      {formatCurrency(BUNDLE_PRICING[type])}/mo
                    </div>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono space-y-1">
                    <div>{bundleSpecs.cpu} • {bundleSpecs.memory}</div>
                    {bundleSpecs.gpu && <div>GPU: {bundleSpecs.gpu}</div>}
                    <div className="text-xs opacity-75">{bundleSpecs.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Operating System Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:uppercase mb-3">
            Operating System
          </label>
          <div className="grid grid-cols-2 gap-3">
            {Object.values(OperatingSystem).map((os) => {
              const isSelected = operatingSystem === os;
              
              return (
                <button
                  key={os}
                  type="button"
                  onClick={() => setOperatingSystem(os)}
                  className={cn(
                    'p-4 border-2 rounded-lg text-center transition-all',
                    isSelected
                      ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20 retro:border-green-500 retro:bg-green-950'
                      : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 retro:border-green-700 retro:hover:border-green-500',
                    'retro:rounded-none'
                  )}
                >
                  <div className="text-4xl mb-2">
                    {os === OperatingSystem.WINDOWS ? '🪟' : '🐧'}
                  </div>
                  <div className="font-semibold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                    {os}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Blueprint Selection (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:uppercase mb-2">
            Blueprint (Optional)
          </label>
          <select
            value={blueprintId}
            onChange={(e) => setBlueprintId(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
          >
            <option value="">No Blueprint (Base Image)</option>
            <option value="blueprint-1">Development Environment</option>
            <option value="blueprint-2">Data Science Stack</option>
            <option value="blueprint-3">DevOps Tools</option>
          </select>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 retro:text-green-600 retro:font-mono">
            Blueprints provide pre-configured software environments
          </p>
        </div>

        {/* Region Selection (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:uppercase mb-2">
            Region (Optional)
          </label>
          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
          >
            <option value="">Auto-select (Recommended)</option>
            <option value="us-east-1">US East (N. Virginia)</option>
            <option value="us-west-2">US West (Oregon)</option>
            <option value="eu-west-1">EU (Ireland)</option>
            <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
          </select>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 retro:text-green-600 retro:font-mono">
            Auto-select chooses the region with lowest latency
          </p>
        </div>

        {/* Cost Estimate */}
        <div className="p-4 bg-gray-50 dark:bg-gray-800 retro:bg-black retro:border retro:border-green-500 rounded-lg retro:rounded-none">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono retro:uppercase">
              Estimated Monthly Cost
            </span>
            <span className="text-2xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:retro-glow">
              {formatCurrency(estimatedCost)}
            </span>
          </div>
          <p className="text-xs text-gray-600 dark:text-gray-400 retro:text-green-600 retro:font-mono">
            Actual costs may vary based on usage. Stopped workspaces incur reduced charges.
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 retro:bg-red-950 border border-red-200 dark:border-red-800 retro:border-red-500 rounded-lg retro:rounded-none">
            <div className="flex items-start gap-2">
              <span className="text-red-600 dark:text-red-400 retro:text-red-500 retro:font-mono">[!]</span>
              <div className="flex-1 text-sm text-red-800 dark:text-red-300 retro:text-red-400 retro:font-mono">
                Failed to provision workspace. Please try again.
              </div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {isSuccess && (
          <div className="p-4 bg-green-50 dark:bg-green-900/20 retro:bg-green-950 border border-green-200 dark:border-green-800 retro:border-green-500 rounded-lg retro:rounded-none">
            <div className="flex items-start gap-2">
              <span className="text-green-600 dark:text-green-400 retro:text-green-500 retro:font-mono">[✓]</span>
              <div className="flex-1 text-sm text-green-800 dark:text-green-300 retro:text-green-400 retro:font-mono">
                Workspace provisioning started! This may take up to 5 minutes.
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 justify-end pt-4 border-t dark:border-gray-700 retro:border-green-500">
          <button
            type="button"
            onClick={onClose}
            disabled={isPending}
            className="px-6 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none retro:hover:bg-green-950 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isPending || isSuccess}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 retro:bg-green-600 retro:border-2 retro:border-green-500 retro:text-black retro:font-mono retro:font-bold retro:rounded-none retro:hover:bg-green-500 disabled:opacity-50"
          >
            {isPending ? (
              <span>
                <span className="retro:hidden">Provisioning...</span>
                <span className="hidden retro:inline">[PROVISIONING...]</span>
              </span>
            ) : (
              <span>
                <span className="retro:hidden">Provision Workspace</span>
                <span className="hidden retro:inline">[PROVISION]</span>
              </span>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
