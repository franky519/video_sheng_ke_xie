import {assets} from '../lib/assets';

export const AssetLedger = ({visible}: {visible: boolean}) => {
  if (!visible) {
    return null;
  }

  return (
    <div className="asset-ledger">
      <div className="asset-ledger-title">资产协议检查</div>
      {assets.map((asset) => (
        <div className="asset-row" key={asset.id}>
          <span className="asset-id">{asset.id}</span>
          <span className={`asset-status ${asset.status === 'AUTO' ? 'asset-auto' : 'asset-todo'}`}>
            {asset.status}
          </span>
          <span className="asset-fallback">{asset.fallback}</span>
        </div>
      ))}
    </div>
  );
};

