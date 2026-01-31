import React, { useState, useEffect } from 'react';
import { FaTable } from 'react-icons/fa';
import './styles/DbTablesTab.css';

interface TableData {
  columns: string[];
  rows: (string | number)[][];
}

const DbTablesTab: React.FC = () => {
  const [dbTables, setDbTables] = useState<string[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableData, setTableData] = useState<TableData>({ columns: [], rows: [] });
  const [loadingTables, setLoadingTables] = useState<boolean>(false);
  const [loadingTableData, setLoadingTableData] = useState<boolean>(false);

  const fetchDbTables = async () => {
    setLoadingTables(true);
    setDbTables([]);
    setSelectedTable(null);
    setTableData({ columns: [], rows: [] });
    try {
      const res = await fetch('http://localhost:8000/list_db_tables/');
      const data: { tables?: string[] } = await res.json();
      setDbTables(data.tables || []);
    } catch {
      setDbTables([]);
    }
    setLoadingTables(false);
  };

  const fetchTableData = async (table: string) => {
    setSelectedTable(table);
    setLoadingTableData(true);
    setTableData({ columns: [], rows: [] });
    try {
      const res = await fetch(`http://localhost:8000/get_table_data/?table=${encodeURIComponent(table)}`);
      const data: TableData = await res.json();
      setTableData({ columns: data.columns || [], rows: data.rows || [] });
    } catch {
      setTableData({ columns: [], rows: [] });
    }
    setLoadingTableData(false);
  };

  // Fetch tables automatically when component mounts
  useEffect(() => {
    fetchDbTables();
  }, []); // Empty dependency array ensures it runs only once on mount

  return (
    <div className="admin-main">
      <div className="db-header">
        <h2 className="db-title">Database Tables</h2>
        {/* Optional: Keep refresh button for manual refresh if needed */}
        <button className="db-refresh-btn" onClick={fetchDbTables} disabled={loadingTables}>
          {loadingTables ? 'Loading...' : 'Refresh Tables'}
        </button>
      </div>
      <div className="db-content">
        {dbTables.length === 0 && !loadingTables && (
          <div className="db-no-data">No tables found.</div>
        )}
        {dbTables.length > 0 && (
          <div className="db-table-grid">
            {dbTables.map((table, idx) => (
              <div
                className={`db-table-card ${selectedTable === table ? 'selected' : ''}`}
                key={table + idx}
                onClick={() => fetchTableData(table)}
              >
                <FaTable className="db-table-icon" />
                <span className="db-table-name">{table}</span>
              </div>
            ))}
          </div>
        )}
        {selectedTable && (
          <div className="db-table-details">
            <h3 className="db-table-details-title">{selectedTable}</h3>
            {loadingTableData ? (
              <div className="db-loading">Loading...</div>
            ) : tableData.columns.length > 0 ? (
              <div className="db-table-wrapper">
                <table className="db-table">
                  <thead>
                    <tr>{tableData.columns.map((col, i) => <th key={i}>{col}</th>)}</tr>
                  </thead>
                  <tbody>
                    {tableData.rows.map((row, i) => (
                      <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="db-no-data">No data.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DbTablesTab;