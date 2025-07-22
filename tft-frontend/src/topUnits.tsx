import React, { useState, useEffect } from 'react';

interface ItemCombo {
  items: string;
  avg_placement: number;
  games: number;
}

interface SynergyTrait {
  trait: string;
  avg_placement: number;
  games: number;
}

interface UnitAnalysis {
  unit_name: string;
  games_analyzed: number;
  item_combinations: ItemCombo[];
  synergy_traits: SynergyTrait[];
  native_traits: string[];
  total_games?: number;
}

interface TopUnitsProps {
  data?: {
    top_units?: UnitAnalysis[];
    total_games_analyzed?: number;
    total_unit_instances?: number;
    riot_id?: string;
    tft_set?: number;
  } | null;
  loading?: boolean;
  hasSearched?: boolean;
}

const TopUnits: React.FC<TopUnitsProps> = ({ data, loading, hasSearched }) => {
  const [unitMeta, setUnitMeta] = useState<any[]>([]);
  const [traitMeta, setTraitMeta] = useState<any[]>([]);
  const [selectedUnit, setSelectedUnit] = useState<string | null>(null);

  useEffect(() => {
    // Fetch unit and trait metadata from Community Dragon API
    fetch('https://raw.communitydragon.org/latest/cdragon/tft/en_us.json')
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        let unitsArray: any[] = [];
        let traitsArray: any[] = [];
        
        if (Array.isArray(data)) {
          unitsArray = data.filter((entry: any) => (
            typeof entry === 'object' &&
            entry?.apiName?.startsWith('TFT14_') &&
            entry?.icon?.includes('champion')
          ));
          traitsArray = data.filter((entry: any) => (
            typeof entry === 'object' &&
            entry?.apiName?.startsWith('TFT14_') &&
            entry?.icon?.includes('Trait_Icon')
          ));
        } else if (typeof data === 'object' && data !== null) {
          // Try to find units and traits in the data structure
          const values = Object.values(data);
          unitsArray = values.filter((entry: any) => (
            typeof entry === 'object' &&
            entry?.apiName?.startsWith('TFT14_') &&
            entry?.icon?.includes('champion')
          )) as any[];
          traitsArray = values.filter((entry: any) => (
            typeof entry === 'object' &&
            entry?.apiName?.startsWith('TFT14_') &&
            entry?.icon?.includes('Trait_Icon')
          )) as any[];
        }
        
        setUnitMeta(unitsArray);
        setTraitMeta(traitsArray);
      })
      .catch((err) => {
        console.error("Failed to load unit and trait metadata:", err);
      });
  }, []);

  const getTraitInfo = (traitKey: string) => {
    // First try with TFT14_ prefix
    let found = traitMeta.find(meta => {
      return meta.apiName === traitKey || 
             meta.apiName.toLowerCase() === traitKey.toLowerCase() || 
             meta.name.toLowerCase() === traitKey.toLowerCase();
    });

    // If not found and doesn't have TFT14_ prefix, try adding it
    if (!found && !traitKey.startsWith('TFT14_')) {
      const prefixedKey = `TFT14_${traitKey}`;
      found = traitMeta.find(meta => {
        return meta.apiName === prefixedKey || 
               meta.apiName.toLowerCase() === prefixedKey.toLowerCase() || 
               meta.name.toLowerCase() === prefixedKey.toLowerCase();
      });
    }

    if (!found) {
      // Clean up trait name for display
      const cleanName = traitKey.replace(/^TFT\d+_/, '').replace(/_/g, ' ');
      return { name: cleanName, icon: '' };
    }

    let iconPath = found.icon;
    iconPath = iconPath.replace(/^ASSETS\//i, '');
    iconPath = iconPath.toLowerCase();
    iconPath = iconPath.replace(/\.tex$/, '.png');
    
    const iconURL = `https://raw.communitydragon.org/latest/game/assets/${iconPath}`;
    
    return { name: found.name, icon: iconURL };
  };

  const getUnitInfo = (unitKey: string) => {
    const found = unitMeta.find(meta => {
      return meta.apiName === unitKey || 
             meta.apiName.toLowerCase() === unitKey.toLowerCase() || 
             meta.name.toLowerCase() === unitKey.toLowerCase();
    });

    if (!found) {
      // Clean up unit name for display
      const cleanName = unitKey.replace(/^TFT\d+_/, '').replace(/_/g, ' ');
      return { name: cleanName, icon: '' };
    }

    let iconPath = found.icon;
    iconPath = iconPath.replace(/^ASSETS\//i, '');
    iconPath = iconPath.toLowerCase();
    iconPath = iconPath.replace(/\.tex$/, '.png');
    
    const iconURL = `https://raw.communitydragon.org/latest/game/assets/${iconPath}`;
    
    return { name: found.name, icon: iconURL };
  };

  const getItemIcon = (itemName: string) => {
    const cleanName = itemName.toLowerCase();
    const iconURL = `https://raw.communitydragon.org/latest/game/assets/maps/tft/icons/items/hexcore/${cleanName}.png`;
    return iconURL;
  };

  const handleItemIconError = (e: React.SyntheticEvent<HTMLImageElement>, itemName: string, attemptIndex: number = 0) => {
    const cleanName = itemName.toLowerCase();
    const possibleSets = ['tft_set13', 'tft_set12', 'tft_set11', 'base', 'default'];
    
    if (attemptIndex < possibleSets.length) {
      const nextURL = `https://raw.communitydragon.org/latest/game/assets/maps/tft/icons/items/hexcore/${cleanName}.${possibleSets[attemptIndex]}.png`;
      e.currentTarget.src = nextURL;
      e.currentTarget.onerror = () => handleItemIconError(e, itemName, attemptIndex + 1);
    } else {
      e.currentTarget.style.display = 'none';
    }
  };

  const cleanItemName = (itemName: string) => {
    return itemName
      .replace(/^tft_item_/i, '')
      .replace(/_/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  const cleanTraitName = (traitName: string) => {
    return traitName
      .replace(/^TFT\d+_/i, '')
      .replace(/_/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  // Show instruction message if no search has been performed
  if (!hasSearched && !loading) {
    return (
      <div className="max-w-6xl mx-auto p-6 bg-white">
        <div className="text-center py-12">
          <div className="mb-6">
            <svg className="mx-auto h-24 w-24 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">TFT Units Performance</h2>
          <p className="text-gray-600 mb-2">Enter your username above and click Search to analyze your unit performance.</p>
          <p className="text-sm text-gray-500">This will show your most played units with their best item combinations and trait synergies in Set 14.</p>
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
          <h2 className="text-xl font-semibold mb-4">Analyzing Units...</h2>
          <div className="text-gray-600">
            <p className="mb-2">Processing your match history and calculating unit performance...</p>
            <p className="text-sm">This may take 30-60 seconds depending on your match history.</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state or no data
  if (!data || !data.top_units) {
    return (
      <div className="max-w-6xl mx-auto p-6 bg-white">
        <div className="text-center py-12">
          <div className="mb-6">
            <svg className="mx-auto h-16 w-16 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h14.856c1.54 0 2.502-1.667 1.732-2.5L14.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold mb-4 text-gray-900">No Unit Data Available</h2>
          <div className="text-gray-600">
            <p>Unable to load unit performance data. This could be due to:</p>
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

  const topUnits = data.top_units || [];
  const selectedUnitData = selectedUnit ? topUnits.find(unit => unit.unit_name === selectedUnit) : null;

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">TFT Units Performance</h1>
        <p className="text-gray-600">Analyze your most played units with best item combinations and trait synergies</p>
      </div>

      {/* Summary Stats */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <div className="text-sm font-medium text-blue-800">Total Games</div>
          <div className="text-2xl font-bold text-blue-900">
            {data.total_games_analyzed || 0}
          </div>
          <div className="text-sm text-blue-700">Set {data.tft_set} matches analyzed</div>
        </div>
        
        <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
          <div className="text-sm font-medium text-green-800">Units Analyzed</div>
          <div className="text-2xl font-bold text-green-900">
            {topUnits.length}
          </div>
          <div className="text-sm text-green-700">Most frequently played units</div>
        </div>

        <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
          <div className="text-sm font-medium text-purple-800">Unit Instances</div>
          <div className="text-2xl font-bold text-purple-900">
            {data.total_unit_instances || 0}
          </div>
          <div className="text-sm text-purple-700">Total units played across all games</div>
        </div>
      </div>

      {/* Units Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {topUnits.map((unit, index) => {
          const unitInfo = getUnitInfo(unit.unit_name);
          const isSelected = selectedUnit === unit.unit_name;
          
          return (
            <div
              key={unit.unit_name}
              className={`bg-white rounded-lg shadow-lg border-2 transition-all duration-200 cursor-pointer ${
                isSelected ? 'border-blue-500 shadow-xl' : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedUnit(isSelected ? null : unit.unit_name)}
            >
              <div className="p-6">
                {/* Unit Header */}
                <div className="flex items-center mb-4">
                  {unitInfo.icon && (
                    <div className="w-12 h-12 rounded-lg overflow-hidden mr-4 bg-gray-800">
                      <img
                        src={unitInfo.icon}
                        alt={unitInfo.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{unitInfo.name}</h3>
                    <p className="text-sm text-gray-500">{unit.games_analyzed} games analyzed</p>
                  </div>
                </div>

                {/* Best Item Combo Preview */}
                {unit.item_combinations.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Best Item Combo:</h4>
                    <div className="flex items-center space-x-2 mb-1">
                      {unit.item_combinations[0].items.split(' | ').map((item, idx) => (
                        <div key={idx} className="w-6 h-6 rounded bg-gray-100 flex items-center justify-center">
                          <img
                            src={getItemIcon(item)}
                            alt={cleanItemName(item)}
                            className="w-full h-full object-contain"
                            onError={(e) => handleItemIconError(e, item)}
                          />
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-gray-600">
                      Avg: {unit.item_combinations[0].avg_placement} ({unit.item_combinations[0].games} games)
                    </p>
                  </div>
                )}

                {/* Best Synergy Preview */}
                {unit.synergy_traits.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Best Trait Combo:</h4>
                    <div className="flex items-center space-x-2 mb-1">
                      {(() => {
                        const traitInfo = getTraitInfo(`TFT14_${unit.synergy_traits[0].trait}`);
                        return (
                          <>
                            {traitInfo.icon && (
                              <div className="w-6 h-6 rounded bg-gray-800 p-1 flex items-center justify-center">
                                <img
                                  src={traitInfo.icon}
                                  alt={traitInfo.name}
                                  className="w-full h-full object-contain"
                                  onError={(e) => {
                                    e.currentTarget.style.display = 'none';
                                  }}
                                />
                              </div>
                            )}
                            <span className="text-sm text-green-600 font-medium">
                              {cleanTraitName(unit.synergy_traits[0].trait)}
                            </span>
                          </>
                        );
                      })()}
                    </div>
                    <p className="text-xs text-gray-600">
                      Avg: {unit.synergy_traits[0].avg_placement} ({unit.synergy_traits[0].games} games)
                    </p>
                  </div>
                )}

                <div className="text-center">
                  <button className={`text-sm px-4 py-2 rounded transition-colors ${
                    isSelected 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}>
                    {isSelected ? 'Hide Details' : 'Show Details'}
                  </button>
                </div>
              </div>

              {/* Expanded Details */}
              {isSelected && selectedUnitData && (
                <div className="border-t border-gray-200 p-6 bg-gray-50">
                  {/* Item Combinations */}
                  <div className="mb-6">
                    <h4 className="text-md font-semibold text-gray-800 mb-3">Top Item Combinations:</h4>
                    <div className="space-y-2">
                      {selectedUnitData.item_combinations.slice(0, 5).map((combo, idx) => (
                        <div key={idx} className="flex items-center justify-between bg-white p-3 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <span className="text-sm font-medium text-gray-500">#{idx + 1}</span>
                            <div className="flex items-center space-x-1">
                              {combo.items.split(' | ').map((item, itemIdx) => (
                                <div key={itemIdx} className="w-8 h-8 rounded bg-gray-100 flex items-center justify-center">
                                  <img
                                    src={getItemIcon(item)}
                                    alt={cleanItemName(item)}
                                    className="w-full h-full object-contain"
                                    onError={(e) => handleItemIconError(e, item)}
                                  />
                                </div>
                              ))}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-semibold text-green-600">
                              {combo.avg_placement.toFixed(1)} avg
                            </div>
                            <div className="text-xs text-gray-500">
                              {combo.games} games
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Trait Synergies */}
                  <div>
                    <h4 className="text-md font-semibold text-gray-800 mb-3">Best Trait Combos:</h4>
                    <div className="space-y-2">
                      {selectedUnitData.synergy_traits.slice(0, 5).map((trait, idx) => (
                        <div key={idx} className="flex items-center justify-between bg-white p-3 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <span className="text-sm font-medium text-gray-500">#{idx + 1}</span>
                            <div className="flex items-center space-x-2">
                              {(() => {
                                const traitInfo = getTraitInfo(`TFT14_${trait.trait}`);
                                return (
                                  <>
                                    {traitInfo.icon && (
                                      <div className="w-8 h-8 rounded bg-gray-800 p-1 flex items-center justify-center">
                                        <img
                                          src={traitInfo.icon}
                                          alt={traitInfo.name}
                                          className="w-full h-full object-contain"
                                          onError={(e) => {
                                            e.currentTarget.style.display = 'none';
                                          }}
                                        />
                                      </div>
                                    )}
                                    <span className="text-sm font-medium text-gray-900">
                                      {cleanTraitName(trait.trait)}
                                    </span>
                                  </>
                                );
                              })()}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-semibold text-green-600">
                              {trait.avg_placement.toFixed(1)} avg
                            </div>
                            <div className="text-xs text-gray-500">
                              {trait.games} games
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Analysis Summary */}
      <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h4 className="font-semibold text-blue-800 mb-2">Analysis Summary</h4>
        <div className="text-sm text-blue-700 space-y-1">
          <p>• Analysis based on Set 14 matches only</p>
          <p>• Only units with 3+ games are analyzed for statistical relevance</p>
          <p>• Item combinations require 3+ games to be shown</p>
          <p>• Average placement: lower is better (1st = 1.0, 8th = 8.0)</p>
          <p>• Native traits are excluded from synergy analysis</p>
        </div>
      </div>
    </div>
  );
};

export default TopUnits;