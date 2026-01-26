import React, { useState, useEffect, useRef } from 'react';
import { getCryptoIcon } from './CryptoIcons';
import '../styles/Watchlist.css'; // Reuse watchlist styles and add modal styles

interface AddSymbolModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (symbolCode: string) => void;
  existingSymbols: string[];
}

// Fixed list of supported symbols
const SUPPORTED_SYMBOLS = [
  { code: 'BTCUSDT', name: 'Bitcoin / USDT' },
  { code: 'ETHUSDT', name: 'Ethereum / USDT' },
  { code: 'BNBUSDT', name: 'BNB / USDT' },
  { code: 'XRPUSDT', name: 'XRP / USDT' },
  { code: 'BTCUSD', name: 'Bitcoin / USD' },
];

export const AddSymbolModal: React.FC<AddSymbolModalProps> = ({ isOpen, onClose, onSelect, existingSymbols }) => {
  const [search, setSearch] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setSearch('');
    }
  }, [isOpen]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Filter based on search only
  const filteredSymbols = SUPPORTED_SYMBOLS.filter(
    s => s.code.toLowerCase().includes(search.toLowerCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="modal-overlay">
      <div className="modal-content" ref={modalRef}>
        <div className="modal-header">
          <h3>Quản lý mã</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-search">
          <input
            ref={inputRef}
            type="text"
            placeholder="Tìm kiếm mã (ví dụ: BTC, ETH...)"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="modal-list">
          {filteredSymbols.length > 0 ? (
            filteredSymbols.map((item) => {
              const isActive = existingSymbols.includes(item.code);
              return (
                <div
                  key={item.code}
                  className="modal-item"
                  onClick={() => onSelect(item.code)}
                >
                  <div className="modal-item-info">
                    <span className="modal-item-icon">{getCryptoIcon(item.code, 24)}</span>
                    <div className="modal-item-text">
                      <span className="modal-item-code">{item.code}</span>
                      <span className="modal-item-name">{item.name}</span>
                    </div>
                  </div>

                  {/* Toggle Switch */}
                  <div className={`modal-toggle ${isActive ? 'active' : ''}`}>
                    <div className="modal-toggle-handle"></div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="no-results">
              Không tìm thấy kết quả hoặc mã đã được thêm
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
