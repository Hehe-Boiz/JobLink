import React from 'react';
import { View, TouchableOpacity, Image } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import CustomText from '../common/CustomText'; // Sửa lại đường dẫn nếu cần
import styles, { COLORS } from '../../styles/Employer/JobApplicantsStyles'; // Import Style vừa tạo

const ApplicantItem = ({ item, onPress }) => {
    
    // Logic màu sắc để riêng trong component cho gọn
    const getStatusColor = (status) => {
        const s = status?.toUpperCase();
        if (s === 'APPROVED' || s === 'OFFERED') return { text: COLORS.success, bg: '#E8FAEF' };
        if (s === 'REJECTED') return { text: COLORS.error, bg: '#FFEBEB' };
        if (s === 'INTERVIEWED') return { text: COLORS.info, bg: '#E6E1FF' };
        return { text: COLORS.warning, bg: '#FFF4E5' };
    };

    const statusStyle = getStatusColor(item.status);

    return (
        <TouchableOpacity
            style={styles.card}
            activeOpacity={0.7}
            onPress={onPress}
        >
            <Image
                source={{ uri: item.candidate_avatar || 'https://via.placeholder.com/100' }}
                style={styles.avatar}
            />
            <View style={styles.content}>
                <View style={styles.rowBetween}>
                    <CustomText style={styles.name} numberOfLines={1}>
                        {item.candidate_name || "Ứng viên ẩn danh"}
                    </CustomText>
                    <View style={[styles.badge, { backgroundColor: statusStyle.bg }]}>
                        <CustomText style={[styles.badgeText, { color: statusStyle.text }]}>
                            {item.status || "Chờ duyệt"}
                        </CustomText>
                    </View>
                </View>

                <View style={styles.infoRow}>
                    <MaterialCommunityIcons name="email-outline" size={14} color={COLORS.secondary} />
                    <CustomText style={styles.email} numberOfLines={1}>
                        {item.candidate_email}
                    </CustomText>
                </View>

                <View style={styles.infoRow}>
                    <MaterialCommunityIcons name="clock-time-four-outline" size={14} color="#AAA6B9" />
                    <CustomText style={styles.date}>
                        {new Date(item.created_date).toLocaleDateString('vi-VN')}
                    </CustomText>
                </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#D1D1D1" />
        </TouchableOpacity>
    );
};

export default ApplicantItem;