import React, { useState } from 'react';

interface ItemStat {
  Item: string;
  "Top 4 Rate": number;
  "Bottom 4 Rate": number;
  "Games Played": number;
}

interface TopItemsProps {
  data?: {
    top_items?: ItemStat[];
    bottom_items?: ItemStat[];
    riot_id?: string;
    tft_set?: number;
  } | null;
  loading?: boolean;
  hasSearched?: boolean;
}

const TopItems: React.FC<TopItemsProps> = ({ data, loading, hasSearched }) => {
  const [activeTab, setActiveTab] = useState<'top' | 'bottom'>('top');

  const getItemIcon = (itemName: string) => {
    // Item names come like "tft_item_bloodthirster" 
    // File format is: tft_item_bloodthirster.anything.png
    const cleanName = itemName.toLowerCase();
    
    // Try multiple common patterns since we can't use wildcards in URLs
    const possibleSets = ['tft_set14', 'tft_set13', 'tft_set12', 'tft_set11', 'base', 'default', ''];
    
    // Return the most likely one (Set 14) and let error handling try others
    const iconURL = `https://raw.communitydragon.org/latest/game/assets/maps/tft/icons/items/hexcore/${cleanName}.tft_set14.png`;
    
    return iconURL;
  };

  // Helper function to try multiple icon URLs on error
  const handleIconError = (e: React.SyntheticEvent<HTMLImageElement>, itemName: string, attemptIndex: number = 0) => {
    const cleanName = itemName.toLowerCase();
    const possibleSets = ['tft_set13', 'tft_set12', 'tft_set11', 'base', 'default'];
    
    if (attemptIndex < possibleSets.length) {
      const nextURL = `https://raw.communitydragon.org/latest/game/assets/maps/tft/icons/items/hexcore/${cleanName}.${possibleSets[attemptIndex]}.png`;
      e.currentTarget.src = nextURL;
      e.currentTarget.onerror = () => handleIconError(e, itemName, attemptIndex + 1);
    } else {
      // If all attempts fail, hide the icon
      e.currentTarget.style.display = 'none';
    }
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
          <h2 className="text-2xl font-bold text-gray-900 mb-4">TFT Items Performance</h2>
          <p className="text-gray-600 mb-2">Enter your username above and click Search to analyze your item performance.</p>
          <p className="text-sm text-gray-500">This will show which items lead to your best and worst placements in Set 14.</p>
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
          <h2 className="text-xl font-semibold mb-4">Analyzing Items...</h2>
          <div className="text-gray-600">
            <p className="mb-2">Processing your match history and calculating item performance...</p>
            <p className="text-sm">This may take 30-60 seconds depending on your match history.</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state or no data
  if (!data || (!data.top_items && !data.bottom_items)) {
    return (
      <div className="max-w-6xl mx-auto p-6 bg-white">
        <div className="text-center py-12">
          <div className="mb-6">
            <svg className="mx-auto h-16 w-16 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h14.856c1.54 0 2.502-1.667 1.732-2.5L14.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold mb-4 text-gray-900">No Item Data Available</h2>
          <div className="text-gray-600">
            <p>Unable to load item performance data. This could be due to:</p>
            <ul className="mt-2 text-sm space-y-1">
              <li>• Not enough Set 14 ranked games played</li>
              <li>• Invalid username or account not found</li>
              <li>• API rate limiting or network issues</li>
            </ul>
            <p className="mt-4">Try searching with a different username or try again later.</p>
          </div>
        </div>
      </div>
    );
  }

  const topItems = data.top_items || [];
  const bottomItems = data.bottom_items || [];
  const currentItems = activeTab === 'top' ? topItems : bottomItems;

  const getRankColor = (index: number, isTop: boolean) => {
    if (index === 0) return isTop ? '#ffd700' : '#ff6b6b'; // Gold for #1 top, Red for #1 bottom
    if (index === 1) return isTop ? '#c0c0c0' : '#ff8e8e'; // Silver for #2
    if (index === 2) return isTop ? '#cd7f32' : '#ffaaaa'; // Bronze for #3
    return 'transparent';
  };

  const renderItemRow = (item: ItemStat, index: number) => {
    const isTop = activeTab === 'top';
    const rankColor = getRankColor(index, isTop);
    const itemIcon = getItemIcon(item.Item);
    
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
            <div className="w-8 h-8 rounded-md p-1 flex items-center justify-center">
              <img 
                src={itemIcon} 
                alt={item.Item}
                className="w-full h-full object-contain"
                onError={(e) => handleIconError(e, item.Item)}
              />
            </div>
            <span className="text-sm font-medium text-gray-900">
              {item.Item.replace(/^tft_item_/i, '').replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center">
            <div className="flex-1">
              <div className={`text-sm font-semibold ${isTop ? 'text-green-600' : 'text-gray-900'}`}>
                {(item["Top 4 Rate"] * 100).toFixed(1)}%
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div 
                  className={`h-2 rounded-full ${isTop ? 'bg-green-500' : 'bg-blue-500'}`}
                  style={{ width: `${item["Top 4 Rate"] * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center">
            <div className="flex-1">
              <div className={`text-sm font-semibold ${!isTop ? 'text-red-600' : 'text-gray-900'}`}>
                {(item["Bottom 4 Rate"] * 100).toFixed(1)}%
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div 
                  className={`h-2 rounded-full ${!isTop ? 'bg-red-500' : 'bg-orange-500'}`}
                  style={{ width: `${item["Bottom 4 Rate"] * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          {item["Games Played"].toLocaleString()}
        </td>
      </tr>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">TFT Items Performance</h1>
        <p className="text-gray-600">Analyze the best and worst performing items in Teamfight Tactics</p>
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
              🏆 Top Performing Items
            </button>
            <button
              onClick={() => setActiveTab('bottom')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                activeTab === 'bottom'
                  ? 'border-red-500 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📉 Worst Performing Items
            </button>
          </nav>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
          <div className="text-sm font-medium text-green-800">Showing</div>
          <div className="text-2xl font-bold text-green-900">
            {activeTab === 'top' ? `Top ${topItems.length}` : `Bottom ${bottomItems.length}`}
          </div>
          <div className="text-sm text-green-700">
            {activeTab === 'top' ? 'Highest top 4 placement items' : 'Highest bottom 4 placement items'}
          </div>
        </div>
        
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <div className="text-sm font-medium text-blue-800">Total Games</div>
          <div className="text-2xl font-bold text-blue-900">
            {currentItems.reduce((sum, item) => sum + item["Games Played"], 0).toLocaleString()}
          </div>
          <div className="text-sm text-blue-700">Across all displayed items</div>
        </div>

        <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
          <div className="text-sm font-medium text-purple-800">Average {activeTab === 'top' ? 'Top 4' : 'Bottom 4'} Rate</div>
          <div className="text-2xl font-bold text-purple-900">
            {currentItems.length > 0 
              ? ((currentItems.reduce((sum, item) => sum + item[activeTab === 'top' ? "Top 4 Rate" : "Bottom 4 Rate"], 0) / currentItems.length) * 100).toFixed(1) + '%'
              : '0%'
            }
          </div>
          <div className="text-sm text-purple-700">For displayed items</div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white shadow-lg rounded-lg overflow-hidden border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Item
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
            {currentItems.map(renderItemRow)}
          </tbody>
        </table>
      </div>

      {/* Analysis Summary */}
      <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h4 className="font-semibold text-blue-800 mb-2">Analysis Summary</h4>
        <div className="text-sm text-blue-700 space-y-1">
          <p>• Analysis based on Set 14 matches only</p>
          <p>• Only items with 10+ appearances are included</p>
          <p>• Top 4 placement = positions 1-4, Bottom 4 = positions 5-8</p>
          <p>• Data refreshed in real-time from your recent matches</p>
        </div>
      </div>
    </div>
  );
};

export default TopItems;