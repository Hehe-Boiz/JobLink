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

export const formatTimeElapsed = (dateString) => {
        if (!dateString) return "Vừa xong";

        const now = new Date();
        const past = new Date(dateString);
        const diffInSeconds = Math.floor((now - past) / 1000);

        if (diffInSeconds < 60) {
            return "Vừa xong";
        }

        const diffInMinutes = Math.floor(diffInSeconds / 60);
        if (diffInMinutes < 60) {
            return `${diffInMinutes} phút trước`;
        }

        const diffInHours = Math.floor(diffInMinutes / 60);
        if (diffInHours < 24) {
            return `${diffInHours} giờ trước`;
        }

        const diffInDays = Math.floor(diffInHours / 24);
        if (diffInDays < 7) {
            return `${diffInDays} ngày trước`;
        }

        const diffInWeeks = Math.floor(diffInDays / 7);
        if (diffInWeeks < 4) {
            return `${diffInWeeks} tuần trước`;
        }

        return `${past.getDate()}/${past.getMonth() + 1}/${past.getFullYear()}`;
    };

export const stripHtmlTags = (html) => {
    if (!html) return "";

    let text = html
        .replace(/<br\s*\/?>/gi, "\n")
        .replace(/<\/p>/gi, "\n\n")
        .replace(/<\/li>/gi, "\n");

    text = text.replace(/<[^>]+>/g, "");

    text = text
        .replace(/&nbsp;/g, " ")
        .replace(/&amp;/g, "&")
        .replace(/&lt;/g, "<")
        .replace(/&gt;/g, ">")
        .replace(/&quot;/g, '"');

    return text.trim();
};