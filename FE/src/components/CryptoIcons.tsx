import React from 'react';

interface IconProps {
  className?: string;
  size?: number;
}

export const BitcoinIcon: React.FC<IconProps> = ({ className, size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <circle cx="16" cy="16" r="16" fill="#F7931A" />
    <path d="M22.6245 13.9143C22.868 12.8727 22.3887 11.9079 21.0567 11.4398L21.4947 9.68285L20.4357 9.41846L20.0034 11.1524C19.7259 11.0833 19.4414 11.0183 19.1601 10.9602L19.5912 9.23126L18.5322 8.96687L18.1066 10.6865C17.9042 10.6409 17.6976 10.596 17.4897 10.5529L17.4912 10.5484L16.0319 10.1818L15.6797 11.5947C15.6797 11.5947 16.6631 11.8203 16.6385 11.8368C16.8973 11.9013 16.9467 12.2198 16.9036 12.4334L16.0305 15.9372C16.0851 15.9522 16.143 15.9701 16.2089 16.0076C16.1422 15.9904 16.0793 15.9701 16.0148 15.9536L15.1953 19.2423C15.1325 19.5587 14.8878 19.6892 14.6185 19.5992C14.6521 19.6172 13.668 19.3712 13.668 19.3712L12.9157 21.1272L14.3764 21.4938C14.6076 21.5516 14.8351 21.604 15.0565 21.6505L14.6212 23.3986L15.6802 23.6629L16.121 21.8953C16.3902 21.9688 16.6542 22.0363 16.9115 22.0993L16.476 23.8488L17.535 24.1132L17.9758 22.3392C20.3701 22.7937 22.1706 22.6617 22.8447 20.7352C23.3871 19.1866 22.8169 18.2893 21.785 17.7575C22.5358 17.585 23.0975 16.9209 23.2381 15.9395C23.2359 15.9388 23.2389 15.9388 22.6245 13.9143ZM20.2526 19.2963C19.7423 21.3413 16.3242 20.7299 15.6198 20.5544L16.353 17.6114C17.0573 17.7877 20.7813 18.0644 20.2526 19.2963ZM20.697 15.109C20.2443 16.9248 17.3828 16.2307 16.7626 16.0754L17.4239 13.4216C18.0434 13.5761 21.196 13.7913 20.697 15.109Z" fill="white" />
  </svg>
);

export const EthereumIcon: React.FC<IconProps> = ({ className, size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <circle cx="16" cy="16" r="16" fill="#627EEA" />
    <path d="M16 6L8.88892 17.8889L16 22.1111L23.1111 17.8889L16 6Z" fill="white" fillOpacity="0.602" />
    <path d="M16 6L16 22.1111L23.1111 17.8889L16 6Z" fill="white" />
    <path d="M16 23.5556L8.88892 19.3333L16 29.5556L23.1111 19.3333L16 23.5556Z" fill="white" fillOpacity="0.602" />
    <path d="M16 29.5556V23.5556L23.1111 19.3333L16 29.5556Z" fill="white" />
    <path d="M16 20.8889L23.1111 16.6667L16 22.1111V20.8889Z" fill="#141414" fillOpacity="0.2" />
    <path d="M8.88892 16.6667L16 20.8889V22.1111L8.88892 16.6667Z" fill="#141414" fillOpacity="0.6" />
  </svg>
);

export const BnbIcon: React.FC<IconProps> = ({ className, size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <circle cx="16" cy="16" r="16" fill="#F3BA2F" />
    <path d="M12.1169 13.4143L16.0021 9.52924L19.8872 13.4143L21.4659 11.8385L16.0021 6.37219L10.5358 11.8385L12.1169 13.4143ZM24.4693 14.8419L22.8879 16.4232L24.4693 18.0044L26.0482 16.4232L24.4693 14.8419ZM16.0021 19.4296L12.1169 15.5445H12.1145L10.5358 17.1232L16.0021 22.5896L21.4659 17.1232L19.8872 15.5445L16.0021 19.4296ZM7.53488 14.8419L5.95361 16.4232L7.53488 18.0044L9.11366 16.4232L7.53488 14.8419ZM16.0021 14.9317L14.5103 16.4232L16.0021 17.9146L17.4913 16.4232L16.0021 14.9317Z" fill="white" />
  </svg>
);

export const XrpIcon: React.FC<IconProps> = ({ className, size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <circle cx="16" cy="16" r="16" fill="#23292F" />
    <path d="M16 11.6664C16.8904 10.7761 18.3338 9.3327 20.3061 7.36035H24.1685L16.0024 15.5265L7.83618 7.36035H11.6986C14.7719 10.4336 15.1118 10.7782 16 11.6664ZM16.0024 16.4694L24.1685 24.6355H20.3061L16 20.3295L11.6986 24.6355H7.83618L16.0024 16.4694Z" fill="white" />
  </svg>
);

export const getCryptoIcon = (code: string, size = 24) => {
  if (code.includes('BTC')) return <BitcoinIcon size={size} />;
  if (code.includes('ETH')) return <EthereumIcon size={size} />;
  if (code.includes('BNB')) return <BnbIcon size={size} />;
  if (code.includes('XRP')) return <XrpIcon size={size} />;
  return <span style={{ fontSize: size, lineHeight: '1' }}>₿</span>; // Fallback
};
