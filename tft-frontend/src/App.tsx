import { useState } from 'react';
import TopTraits from './topTraits';
import TopItems from './topItems';
import TopUnits from './topUnits';

function App() {
  const [activeTab, setActiveTab] = useState('traits');
  const [gameName, setGameName] = useState('');
  const [tagLine, setTagLine] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [traitsData, setTraitsData] = useState(null);
  const [itemsData, setItemsData] = useState(null);
  const [unitsData, setUnitsData] = useState(null);

  const handleSearch = async () => {
    if (!gameName.trim() || !tagLine.trim()) {
      setError('Please enter both Game Name and Tag Line');
      return;
    }

    setLoading(true);
    setError('');
    setTraitsData(null);
    setItemsData(null);
    setUnitsData(null);

    try {
      const baseUrl = 'https://tft-stat-tool.onrender.com';
      const params = `gameName=${encodeURIComponent(gameName.trim())}&tagLine=${encodeURIComponent(tagLine.trim())}`;
      
      const response = await fetch(`${baseUrl}/analyze-all-riot-id?${params}`, { method: 'GET' });
      
      if (response.ok) {
        const data = await response.json();
        
        // DEBUG: Log the entire response
        console.log('FULL RESPONSE:', JSON.stringify(data, null, 2));
        console.log('Units section:', data.units);
        console.log('Units success:', data.units?.success);
        console.log('Units top_units:', data.units?.top_units);
        
        // Extract individual analysis results
        if (data.traits && data.traits.success) {
          setTraitsData({
            top_traits: data.traits.top_traits,
            bottom_traits: data.traits.bottom_traits,
            riot_id: data.riot_id,
            tft_set: data.tft_set
          });
        }
        
        if (data.items && data.items.success) {
          setItemsData({
            top_items: data.items.top_items,
            bottom_items: data.items.bottom_items,
            riot_id: data.riot_id,
            tft_set: data.tft_set
          });
        }
        
        // Units data
        console.log('Checking units data...');
        console.log('data.units exists:', !!data.units);
        console.log('data.units.success:', data.units?.success);
        console.log('data.units.top_units exists:', !!data.units?.top_units);
        console.log('data.units.top_units length:', data.units?.top_units?.length);
        
        if (data.units && data.units.success) {
          console.log('Setting units data - SUCCESS PATH');
          const unitsDataToSet = {
            top_units: data.units.top_units,
            total_games_analyzed: data.units.total_games_analyzed,
            total_unit_instances: data.units.total_unit_instances,
            riot_id: data.riot_id,
            tft_set: data.tft_set
          };
          console.log('unitsDataToSet:', unitsDataToSet);
          setUnitsData(unitsDataToSet);
          console.log('Units data successfully set:', unitsDataToSet);
        } else if (data.units) {
          console.log('Setting units data - FALLBACK PATH (no success check)');
          const unitsDataToSet = {
            top_units: data.units.top_units || [],
            total_games_analyzed: data.units.total_games_analyzed || 0,
            total_unit_instances: data.units.total_unit_instances || 0,
            riot_id: data.riot_id,
            tft_set: data.tft_set
          };
          console.log('unitsDataToSet (fallback):', unitsDataToSet);
          setUnitsData(unitsDataToSet);
        } else if (data.top_units) {
          const unitsDataToSet = {
            top_units: data.top_units,
            total_games_analyzed: data.total_games_analyzed,
            total_unit_instances: data.total_unit_instances,
            riot_id: data.riot_id,
            tft_set: data.tft_set
          };
          setUnitsData(unitsDataToSet);
        }
        
        // Switch to first successful tab
        if (data.traits && data.traits.success) {
          setActiveTab('traits');
        } else if (data.items && data.items.success) {
          setActiveTab('items');
        } else if (data.units && data.units.top_units !== undefined) {
          setActiveTab('units');
        }
        
      } else {
        const errorText = await response.text();
        throw new Error(`Analysis failed: ${response.status} - ${errorText}`);
      }
      
    } catch (err) {
      console.error('Full error details:', err);
      setError(err.message || 'Analysis failed. Please check your Riot ID and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="min-h-screen bg-white text-gray-900 p-8">
      <h1 className="text-3xl font-bold text-center mb-4">TFT Stat Tool</h1>
       
      <div className="flex flex-col items-center mb-4">
        <div className="mb-4 text-center">
          <label className="block text-sm font-medium mb-2">Riot ID</label>
          <div className="flex items-center gap-2">
            <input 
              type="text" 
              className="input input-bordered input-sm w-40" 
              placeholder="Game Name"
              value={gameName}
              onChange={(e) => setGameName(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            <span className="text-lg font-bold">#</span>
            <input 
              type="text" 
              className="input input-bordered input-sm w-20" 
              placeholder="Tag"
              value={tagLine}
              onChange={(e) => setTagLine(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Example: VIT k3soju#000
          </div>
        </div>
        
        <button 
          className={`btn btn-primary btn-sm ${loading ? 'loading' : ''}`}
          onClick={handleSearch}
          disabled={loading || !gameName.trim() || !tagLine.trim()}
        >
          {loading ? 'Analyzing...' : 'Search'}
        </button>
        
        {/* Error Display */}
        {error && (
          <div className="alert alert-error mt-4 max-w-md">
            <div>
              <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        )}
      </div>
       
      <div role="tablist" className="tabs tabs-lifted justify-center">
        <button 
          role="tab" 
          className={`tab ${activeTab === 'traits' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('traits')}
          disabled={loading}
        >
          Traits
        </button>
        <button 
          role="tab" 
          className={`tab ${activeTab === 'items' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('items')}
          disabled={loading}
        >
          Items
        </button>
        <button 
          role="tab" 
          className={`tab ${activeTab === 'units' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('units')}
          disabled={loading}
        >
          Units
        </button>
      </div>

      {/* Tab Content */}
      <div className="mt-8 p-6 bg-gray-50 rounded-lg">
        {activeTab === 'traits' && (
          <TopTraits 
            data={traitsData} 
            loading={loading}
            hasSearched={!!traitsData || !!error}
          />
        )}
        {activeTab === 'items' && (
          <TopItems 
            data={itemsData} 
            loading={loading}
            hasSearched={!!itemsData || !!error}
          />
        )}
        {activeTab === 'units' && (
          <TopUnits 
            data={unitsData} 
            loading={loading}
            hasSearched={!!unitsData || !!error}
          />
        )}
      </div>
    </div>
  );
}

export default App;