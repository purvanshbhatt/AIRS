import { useState, useEffect } from 'react';
import {
    Plus,
    Map,
    CheckCircle2,
    Circle,
    Clock,
    Trash2,
} from 'lucide-react';
import {
    Card,
    CardHeader,
    CardTitle,
    CardContent,
    Button,
} from './ui';
import { getRoadmap, createRoadmapItem, updateRoadmapItem, deleteRoadmapItem } from '../api';
import type { TrackerItem } from '../types';

interface RoadmapTrackerProps {
    organizationId: string;
}

export function RoadmapTracker({ organizationId }: RoadmapTrackerProps) {
    const [items, setItems] = useState<TrackerItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);
    const [newItemTitle, setNewItemTitle] = useState('');

    // Load items
    useEffect(() => {
        loadItems();
    }, [organizationId]);

    const loadItems = async () => {
        try {
            const res = await getRoadmap(organizationId);
            setItems(res.items);
        } catch (e) {
            console.error("Failed to load roadmap", e);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async () => {
        if (!newItemTitle.trim()) return;
        try {
            const newItem = await createRoadmapItem(organizationId, {
                title: newItemTitle,
                status: 'todo',
                priority: 'medium',
                effort: 'medium'
            });
            setItems([newItem, ...items]);
            setNewItemTitle('');
            setIsAdding(false);
        } catch (e) {
            console.error(e);
        }
    };

    const handleToggleStatus = async (item: TrackerItem) => {
        const newStatus = item.status === 'done' ? 'todo' : 'done';
        try {
            const updated = await updateRoadmapItem(item.id, { status: newStatus });
            setItems(items.map(i => i.id === item.id ? updated : i));
        } catch (e) {
            console.error(e);
        }
    };

    const handleDelete = async (id: string) => {
        try {
            await deleteRoadmapItem(id);
            setItems(items.filter(i => i.id !== id));
        } catch (e) {
            console.error(e);
        }
    };

    const pendingItems = items.filter(i => i.status !== 'done');
    const completedItems = items.filter(i => i.status === 'done');

    const getPriorityColor = (p: string) => {
        switch (p) {
            case 'high': return 'text-red-600 bg-red-50';
            case 'medium': return 'text-yellow-600 bg-yellow-50';
            case 'low': return 'text-blue-600 bg-blue-50';
            default: return 'text-gray-600 bg-gray-50';
        }
    };

    return (
        <Card className="h-full flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                    <Map className="w-5 h-5 text-primary-600" />
                    Roadmap Tracker
                </CardTitle>
                <Button size="sm" variant="ghost" onClick={() => setIsAdding(!isAdding)}>
                    <Plus className="w-4 h-4 mr-1" /> Add Item
                </Button>
            </CardHeader>
            <CardContent className="flex-1 overflow-auto pr-2">

                {isAdding && (
                    <div className="flex gap-2 mb-4 animate-in slide-in-from-top-2">
                        <input
                            autoFocus
                            className="flex-1 border border-gray-300 rounded-md px-3 py-1.5 text-sm"
                            placeholder="What needs to be done?"
                            value={newItemTitle}
                            onChange={e => setNewItemTitle(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleAdd()}
                        />
                        <Button size="sm" onClick={handleAdd}>Add</Button>
                    </div>
                )}

                <div className="space-y-4">
                    {items.length === 0 && !loading && !isAdding && (
                        <div className="text-center py-8 text-gray-500 text-sm">
                            <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                            No items yet. Add one to start tracking progress.
                        </div>
                    )}

                    {/* Pending */}
                    <div className="space-y-2">
                        {pendingItems.map(item => (
                            <div key={item.id} className="group flex items-start gap-3 p-3 bg-white border border-gray-100 rounded-lg hover:border-gray-300 transition-all shadow-sm">
                                <button
                                    onClick={() => handleToggleStatus(item)}
                                    className="mt-0.5 text-gray-400 hover:text-green-600 transition-colors"
                                >
                                    <Circle className="w-5 h-5" />
                                </button>
                                <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium text-gray-900">{item.title}</div>
                                    <div className="flex items-center gap-2 mt-1">
                                        <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${getPriorityColor(item.priority)}`}>
                                            {item.priority}
                                        </span>
                                        {item.effort && (
                                            <span className="text-xs text-gray-400">• {item.effort} effort</span>
                                        )}
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleDelete(item.id)}
                                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* Completed */}
                    {completedItems.length > 0 && (
                        <>
                            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-4">Completed</div>
                            <div className="space-y-2 opacity-60">
                                {completedItems.map(item => (
                                    <div key={item.id} className="flex items-center gap-3 p-2">
                                        <button onClick={() => handleToggleStatus(item)} className="text-green-600">
                                            <CheckCircle2 className="w-5 h-5" />
                                        </button>
                                        <div className="flex-1 text-sm text-gray-500 line-through decoration-gray-400">
                                            {item.title}
                                        </div>
                                        <button
                                            onClick={() => handleDelete(item.id)}
                                            className="text-gray-300 hover:text-red-500"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
