import { useNavigate } from 'react-router-dom';
import '../styles/NotFound.css';

export const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className="notfound-container">
      <div className="notfound-content">
        <h1 className="notfound-code">404</h1>
        <h2 className="notfound-title">Trang không tồn tại</h2>
        <p className="notfound-description">
          Rất tiếc, trang bạn đang tìm kiếm không tồn tại hoặc đã bị xóa.
        </p>
        <div className="notfound-actions">
          <button className="btn-primary" onClick={() => navigate('/')}>
            Về trang chủ
          </button>
          <button className="btn-secondary" onClick={() => navigate(-1)}>
            Quay lại
          </button>
        </div>
      </div>
    </div>
  );
};
