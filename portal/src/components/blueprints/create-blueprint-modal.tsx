/**
 * Create Blueprint Modal Component
 * 
 * Requirements: 2.1, 2.2
 */

'use client';

import { useState } from 'react';
import { useCreateBlueprint } from '@/hooks/use-blueprints';
import { Modal } from '@/components/ui/modal';
import { OperatingSystem } from '@/types';

interface CreateBlueprintModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CreateBlueprintModal({ isOpen, onClose }: CreateBlueprintModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [operatingSystem, setOperatingSystem] = useState<OperatingSystem>(OperatingSystem.WINDOWS);
  const [softwareInput, setSoftwareInput] = useState('');
  const [softwareList, setSoftwareList] = useState<string[]>([]);
  const [teamId, setTeamId] = useState<string>('');
  const [isTeamBlueprint, setIsTeamBlueprint] = useState(false);

  const createMutation = useCreateBlueprint();

  const handleAddSoftware = () => {
    const trimmed = softwareInput.trim();
    if (trimmed && !softwareList.includes(trimmed)) {
      setSoftwareList([...softwareList, trimmed]);
      setSoftwareInput('');
    }
  };

  const handleRemoveSoftware = (software: string) => {
    setSoftwareList(softwareList.filter((s) => s !== software));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim() || !description.trim() || softwareList.length === 0) {
      return;
    }

    createMutation.mutate(
      {
        name: name.trim(),
        description: description.trim(),
        operating_system: operatingSystem,
        software_manifest: softwareList,
        ...(isTeamBlueprint && teamId ? { team_id: teamId } : {}),
      },
      {
        onSuccess: () => {
          // Reset form
          setName('');
          setDescription('');
          setOperatingSystem(OperatingSystem.WINDOWS);
          setSoftwareInput('');
          setSoftwareList([]);
          setTeamId('');
          setIsTeamBlueprint(false);
          onClose();
        },
      }
    );
  };

  const handleClose = () => {
    if (!createMutation.isPending) {
      onClose();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create Blueprint" size="lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-2">
            <span className="retro:hidden">Blueprint Name</span>
            <span className="hidden retro:inline">[NAME]</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Python Development Environment"
            required
            className="w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none focus:ring-2 focus:ring-blue-500 retro:focus:ring-green-500"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-2">
            <span className="retro:hidden">Description</span>
            <span className="hidden retro:inline">[DESCRIPTION]</span>
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what this blueprint includes and its intended use..."
            required
            rows={3}
            className="w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none focus:ring-2 focus:ring-blue-500 retro:focus:ring-green-500"
          />
        </div>

        {/* Operating System */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-2">
            <span className="retro:hidden">Operating System</span>
            <span className="hidden retro:inline">[OPERATING SYSTEM]</span>
          </label>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setOperatingSystem(OperatingSystem.WINDOWS)}
              className={`p-4 border-2 rounded-lg transition-all retro:rounded-none ${
                operatingSystem === OperatingSystem.WINDOWS
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 retro:border-green-500 retro:bg-green-950'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 retro:border-green-700 retro:hover:border-green-500'
              }`}
            >
              <div className="text-4xl mb-2 retro:hidden">🪟</div>
              <div className="hidden retro:block text-green-500 text-2xl font-mono mb-2">[WIN]</div>
              <div className="font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                Windows
              </div>
            </button>
            <button
              type="button"
              onClick={() => setOperatingSystem(OperatingSystem.LINUX)}
              className={`p-4 border-2 rounded-lg transition-all retro:rounded-none ${
                operatingSystem === OperatingSystem.LINUX
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 retro:border-green-500 retro:bg-green-950'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 retro:border-green-700 retro:hover:border-green-500'
              }`}
            >
              <div className="text-4xl mb-2 retro:hidden">🐧</div>
              <div className="hidden retro:block text-green-500 text-2xl font-mono mb-2">[LNX]</div>
              <div className="font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                Linux
              </div>
            </button>
          </div>
        </div>

        {/* Software Manifest */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-2">
            <span className="retro:hidden">Software Packages</span>
            <span className="hidden retro:inline">[SOFTWARE PACKAGES]</span>
          </label>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={softwareInput}
              onChange={(e) => setSoftwareInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddSoftware();
                }
              }}
              placeholder="e.g., Python 3.11, Docker, VS Code"
              className="flex-1 px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none focus:ring-2 focus:ring-blue-500 retro:focus:ring-green-500"
            />
            <button
              type="button"
              onClick={handleAddSoftware}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 retro:bg-green-900 retro:border retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none retro:hover:bg-green-800"
            >
              <span className="retro:hidden">Add</span>
              <span className="hidden retro:inline">[ADD]</span>
            </button>
          </div>

          {/* Software List */}
          {softwareList.length > 0 && (
            <div className="flex flex-wrap gap-2 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800 retro:bg-black retro:border-green-500 retro:rounded-none">
              {softwareList.map((software, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 px-3 py-1 bg-white dark:bg-gray-700 border rounded retro:bg-black retro:border-green-500 retro:rounded-none"
                >
                  <span className="text-sm text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                    {software}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleRemoveSoftware(software)}
                    className="text-red-600 hover:text-red-700 retro:text-red-500 retro:hover:text-red-400 retro:font-mono"
                  >
                    <span className="retro:hidden">×</span>
                    <span className="hidden retro:inline">[X]</span>
                  </button>
                </div>
              ))}
            </div>
          )}

          {softwareList.length === 0 && (
            <p className="text-sm text-gray-500 dark:text-gray-400 retro:text-green-600 retro:font-mono">
              <span className="retro:hidden">Add at least one software package</span>
              <span className="hidden retro:inline">[ADD SOFTWARE PACKAGES]</span>
            </p>
          )}
        </div>

        {/* Team Access Control */}
        <div>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={isTeamBlueprint}
              onChange={(e) => setIsTeamBlueprint(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 retro:accent-green-500"
            />
            <div>
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono">
                <span className="retro:hidden">Team Blueprint</span>
                <span className="hidden retro:inline">[TEAM BLUEPRINT]</span>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                <span className="retro:hidden">
                  Only visible to your team members. Uncheck for global visibility.
                </span>
                <span className="hidden retro:inline">
                  [TEAM ONLY. UNCHECK FOR GLOBAL ACCESS]
                </span>
              </div>
            </div>
          </label>
        </div>

        {/* Error Message */}
        {createMutation.isError && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded retro:bg-black retro:border-red-500 retro:rounded-none">
            <p className="text-sm text-red-600 dark:text-red-400 retro:text-red-500 retro:font-mono">
              <span className="retro:hidden">Failed to create blueprint. Please try again.</span>
              <span className="hidden retro:inline">[ERROR: CREATION FAILED. RETRY.]</span>
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 justify-end pt-4 border-t dark:border-gray-700 retro:border-green-500">
          <button
            type="button"
            onClick={handleClose}
            disabled={createMutation.isPending}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none retro:hover:bg-green-950 disabled:opacity-50"
          >
            <span className="retro:hidden">Cancel</span>
            <span className="hidden retro:inline">[CANCEL]</span>
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending || !name.trim() || !description.trim() || softwareList.length === 0}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed retro:bg-green-600 retro:border retro:border-green-500 retro:text-black retro:font-mono retro:rounded-none retro:hover:bg-green-500"
          >
            <span className="retro:hidden">
              {createMutation.isPending ? 'Creating...' : 'Create Blueprint'}
            </span>
            <span className="hidden retro:inline">
              {createMutation.isPending ? '[CREATING...]' : '[CREATE BLUEPRINT]'}
            </span>
          </button>
        </div>
      </form>
    </Modal>
  );
}
