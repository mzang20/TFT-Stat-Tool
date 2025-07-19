import React, { useEffect, useState } from 'react';

interface TraitStat {
  Trait: string;
  "Top 4 Rate": number;
  "Bottom 4 Rate": number;
  "Games Played": number;
}

interface TraitMeta {
  apiName: string;
  name: string;
  icon: string;
}

interface TopTraitsProps {
  data?: {
    top_traits?: TraitStat[];
    bottom_traits?: TraitStat[];
  } | null;
  loading?: boolean;
  hasSearched?: boolean;
}

const TopTraits: React.FC<TopTraitsProps> = ({ data, loading, hasSearched }) => {
  const [traitMeta, setTraitMeta] = useState<TraitMeta[]>([]);
  const [activeTab, setActiveTab] = useState<'top' | 'bottom'>('top');

  useEffect(() => {
    fetch('https://raw.communitydragon.org/latest/cdragon/tft/en_us.json')
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        let traitsArray: TraitMeta[] = [];
        
        if (Array.isArray(data)) {
          traitsArray = data.filter((entry: any) => (
            typeof entry === 'object' &&
            entry?.apiName?.startsWith('TFT14_') &&
            entry?.icon?.includes('Trait_Icon')
          )) as TraitMeta[];
        } else if (typeof data === 'object' && data !== null) {
          if (data.setData && Array.isArray(data.setData)) {
            const set14 = data.setData.find((set: any) => 
              set.number === 14 || set.name?.includes('14') || set.name?.toLowerCase().includes('thirteen')
            );
            
            if (set14 && set14.traits && Array.isArray(set14.traits)) {
              traitsArray = set14.traits.filter((entry: any) => (
                typeof entry === 'object' &&
                entry?.apiName?.startsWith('TFT14_') &&
                entry?.icon?.includes('Trait_Icon')
              )) as TraitMeta[];
            }
          } else {
            const values = Object.values(data);
            traitsArray = values.filter((entry: any) => (
              typeof entry === 'object' &&
              entry?.apiName?.startsWith('TFT14_') &&
              entry?.icon?.includes('Trait_Icon')
            )) as TraitMeta[];
          }
        }
        
        setTraitMeta(traitsArray);
      })
      .catch((err) => {
        console.error("Failed to load en_us.json:", err);
      });
  }, []);

  const getTraitInfo = (traitKey: string) => {
    const found = traitMeta.find(meta => {
      return meta.apiName === traitKey || 
             meta.apiName.toLowerCase() === traitKey.toLowerCase() || 
             meta.name.toLowerCase() === traitKey.toLowerCase();
    });

    if (!found) {
      return { name: traitKey, icon: '' };
    }

    let iconPath = found.icon;
    iconPath = iconPath.replace(/^ASSETS\//i, '');
    iconPath = iconPath.toLowerCase();
    iconPath = iconPath.replace(/\.tex$/, '.png');
    
    const iconURL = `https://raw.communitydragon.org/latest/game/assets/${iconPath}`;
    
    return { name: found.name, icon: iconURL };
  };

  // Show instruction message if no search has been performed
  if (!hasSearched && !loading) {
    return (
      <div className="max-w-6xl mx-auto p-6 bg-white">
        <div className="text-center py-12">
          <div className="mb-6">
            <svg className="mx-auto h-24 w-24 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">TFT Traits Performance</h2>
          <p className="text-gray-600 mb-2">Enter your PUUID above and click Search to analyze your trait performance.</p>
          <p className="text-sm text-gray-500">This will show which traits lead to your best and worst placements in Set 14.</p>
        </div>
      </div>
    );
  }

  // Show loading state
  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6 bg-white">
        <div className="text-center py-12">
          <div className="mb-6">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          </div>
          <h2 className="text-xl font-semibold mb-4">Analyzing Traits...</h2>
          <div className="text-gray-600">
            <p className="mb-2">Processing your match history and calculating trait performance...</p>
            <p className="text-sm">This may take 30-60 seconds depending on your match history.</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state or no data
  if (!data || (!data.top_traits && !data.bottom_traits)) {
    return (
      <div className="max-w-6xl mx-auto p-6 bg-white">
        <div className="text-center py-12">
          <div className="mb-6">
            <svg className="mx-auto h-16 w-16 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h14.856c1.54 0 2.502-1.667 1.732-2.5L14.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold mb-4 text-gray-900">No Trait Data Available</h2>
          <div className="text-gray-600">
            <p>Unable to load trait performance data. This could be due to:</p>
            <ul className="mt-2 text-sm space-y-1">
              <li>• Not enough Set 14 ranked games played</li>
              <li>• Invalid PUUID or account not found</li>
              <li>• API rate limiting or network issues</li>
            </ul>
            <p className="mt-4">Try searching with a different PUUID or try again later.</p>
          </div>
        </div>
      </div>
    );
  }

  const topTraits = data.top_traits || [];
  const bottomTraits = data.bottom_traits || [];
  const currentTraits = activeTab === 'top' ? topTraits : bottomTraits;

  const getRankColor = (index: number, isTop: boolean) => {
    if (index === 0) return isTop ? '#ffd700' : '#ff6b6b'; // Gold for #1 top, Red for #1 bottom
    if (index === 1) return isTop ? '#c0c0c0' : '#ff8e8e'; // Silver for #2
    if (index === 2) return isTop ? '#cd7f32' : '#ffaaaa'; // Bronze for #3
    return 'transparent';
  };

  const renderTraitRow = (trait: TraitStat, index: number) => {
    const info = getTraitInfo(trait.Trait);
    const isTop = activeTab === 'top';
    const rankColor = getRankColor(index, isTop);
    
    return (
      <tr 
        key={index}
        className="hover:bg-gray-50 transition-colors duration-200"
        style={{ backgroundColor: index < 3 ? `${rankColor}20` : undefined }}
      >
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center gap-3">
            <div 
              className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white"
              style={{ backgroundColor: rankColor || '#6b7280' }}
            >
              {index + 1}
            </div>
            {info.icon && (
              <div className="w-8 h-8 rounded-md bg-gray-800 p-1 flex items-center justify-center">
                <img 
                  src={info.icon} 
                  alt={info.name}
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
              </div>
            )}
            <span className="text-sm font-medium text-gray-900">{info.name}</span>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center">
            <div className="flex-1">
              <div className={`text-sm font-semibold ${isTop ? 'text-green-600' : 'text-gray-900'}`}>
                {(trait["Top 4 Rate"] * 100).toFixed(1)}%
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div 
                  className={`h-2 rounded-full ${isTop ? 'bg-green-500' : 'bg-blue-500'}`}
                  style={{ width: `${trait["Top 4 Rate"] * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center">
            <div className="flex-1">
              <div className={`text-sm font-semibold ${!isTop ? 'text-red-600' : 'text-gray-900'}`}>
                {(trait["Bottom 4 Rate"] * 100).toFixed(1)}%
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div 
                  className={`h-2 rounded-full ${!isTop ? 'bg-red-500' : 'bg-orange-500'}`}
                  style={{ width: `${trait["Bottom 4 Rate"] * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          {trait["Games Played"].toLocaleString()}
        </td>
      </tr>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">TFT Traits Performance</h1>
        <p className="text-gray-600">Analyze the best and worst performing traits in Teamfight Tactics</p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('top')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                activeTab === 'top'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🏆 Top Performing Traits
            </button>
            <button
              onClick={() => setActiveTab('bottom')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                activeTab === 'bottom'
                  ? 'border-red-500 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📉 Worst Performing Traits
            </button>
          </nav>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
          <div className="text-sm font-medium text-green-800">Showing</div>
          <div className="text-2xl font-bold text-green-900">
            {activeTab === 'top' ? `Top ${topTraits.length}` : `Bottom ${bottomTraits.length}`}
          </div>
          <div className="text-sm text-green-700">
            {activeTab === 'top' ? 'Highest top 4 placement traits' : 'Highest bottom 4 placement traits'}
          </div>
        </div>
        
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <div className="text-sm font-medium text-blue-800">Total Games</div>
          <div className="text-2xl font-bold text-blue-900">
            {currentTraits.reduce((sum, trait) => sum + trait["Games Played"], 0).toLocaleString()}
          </div>
          <div className="text-sm text-blue-700">Across all displayed traits</div>
        </div>

        <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
          <div className="text-sm font-medium text-purple-800">Average {activeTab === 'top' ? 'Top 4' : 'Bottom 4'} Rate</div>
          <div className="text-2xl font-bold text-purple-900">
            {currentTraits.length > 0 
              ? ((currentTraits.reduce((sum, trait) => sum + trait[activeTab === 'top' ? "Top 4 Rate" : "Bottom 4 Rate"], 0) / currentTraits.length) * 100).toFixed(1) + '%'
              : '0%'
            }
          </div>
          <div className="text-sm text-purple-700">For displayed traits</div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white shadow-lg rounded-lg overflow-hidden border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Trait
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Top 4 Placement
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Bottom 4 Placement
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Games Played
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {currentTraits.map(renderTraitRow)}
          </tbody>
        </table>
      </div>

      {/* Analysis Summary */}
      <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h4 className="font-semibold text-blue-800 mb-2">Analysis Summary</h4>
        <div className="text-sm text-blue-700 space-y-1">
          <p>• Analysis based on Set 14 matches only</p>
          <p>• Only traits with 10+ appearances are included</p>
          <p>• Top 4 placement = positions 1-4, Bottom 4 = positions 5-8</p>
          <p>• Data refreshed in real-time from your recent matches</p>
        </div>
      </div>
    </div>
  );
};

export default TopTraits;