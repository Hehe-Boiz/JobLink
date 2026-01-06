import moment from 'moment'; 

export const formatCurrency = (amount) => {
    if (!amount) return 'Thỏa thuận';
    return amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
};


export const formatCurrencyShort = (amount) => {
    if (!amount) return '0';
    if (amount >= 1000000) {
        return (amount / 1000000).toFixed(1).replace(/\.0$/, '') + ' Triệu';
    }
    return formatCurrency(amount);
};


export const formatDate = (dateString) => {
    if (!dateString) return 'Không thời hạn';
    return moment(dateString).format('DD/MM/YYYY');
};


export const getJobStatus = (deadline) => {
    if (!deadline) return { label: 'Đang tuyển', color: '#00C566', bg: '#E8FAEF' };
    
    const now = new Date();
    const dead = new Date(deadline);
    
    if (dead < now) {
        return { label: 'Hết hạn', color: '#FF4D4D', bg: '#FFECEC' };
    }

    const diffTime = Math.abs(dead - now);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
    if (diffDays <= 3) {
        return { label: 'Sắp hết hạn', color: '#FF9228', bg: '#FFF4E5' };
    }

    return { label: 'Đang tuyển', color: '#00C566', bg: '#E8FAEF' };
};