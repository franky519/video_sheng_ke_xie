type PhoneMockProps = {
  variant: 'plain' | 'expert';
};

const plainLines = [
  '本产品保障多种重大疾病，等待期为90天。',
  '赔付比例依据合同条款约定执行。',
  '建议仔细阅读保险责任与免责条款。',
  '如有疑问请咨询官方客服。',
];

const expertLines = [
  '先看 3 个坑：',
  '免责条款是否把既往症排除。',
  '赔付条件看似相同，触发标准不同。',
  '附录小字可能限制报销范围。',
];

export const PhoneMock = ({variant}: PhoneMockProps) => {
  const isExpert = variant === 'expert';
  const lines = isExpert ? expertLines : plainLines;

  return (
    <div className="phone" data-asset-id="ASSET_01_01">
      <div className="phone-island" />
      <div className="phone-screen">
        <div className="phone-header">
          <div className="doubao-dot" />
          <span>豆包</span>
        </div>
        <div className="phone-content">
          <div className={`phone-title ${isExpert ? 'phone-title-expert' : ''}`}>
            {isExpert ? '专家回答' : '普通回答'}
          </div>
          {lines.map((line, index) => (
            <div
              className={[
                'phone-bubble',
                isExpert ? 'phone-bubble-expert' : 'phone-bubble-plain',
                isExpert && index === 2 ? 'phone-bubble-warning' : '',
              ].join(' ')}
              data-asset-id={isExpert ? 'ASSET_01_03' : 'ASSET_01_02'}
              key={line}
            >
              {line}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

