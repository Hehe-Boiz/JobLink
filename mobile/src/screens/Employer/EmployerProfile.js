


import React, { useContext, useState } from 'react';
import { View, Text, ScrollView, Image, TouchableOpacity, Switch, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { MyUserContext } from '../../utils/contexts/MyContext';
import styles from '../../styles/Employer/EmployerStyles';
import { useDialog } from '../../hooks/useDialog';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Apis, { endpoints } from '../../utils/Apis';
import { useEmployer } from '../../hooks/useEmployer';
import { CLIENT_ID, CLIENT_SECRET } from '@env';//id
const EmployerProfile = ({ navigation }) => {
    const { showDialog } = useDialog();
   
    const [isNotiEnabled, setIsNotiEnabled] = useState(true);
    const [user, dispatch] = useContext(MyUserContext);
    const { profile, clearEmployerProfile } = useEmployer();
    const logout = async () => {
        try {
            console.log(CLIENT_ID);
            console.log(CLIENT_SECRET);
            const token = await AsyncStorage.getItem('token');
            if (token) {
                await Apis.post(endpoints['logout'], {
                    'token': token,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                });
            }
        } catch (ex) {
            console.error("Lỗi revoke token:", ex);
        } finally {
            await AsyncStorage.removeItem('token');
            dispatch({ type: "logout" });
            clearEmployerProfile();
            navigation.reset({
                index: 0,
                routes: [{ name: 'Login' }],
            });
        }
    };
    const handleLogout = () => {
        showDialog({
            type: 'warning',
            title: 'Đăng xuất',
            content: 'Bạn có chắc chắn muốn đăng xuất?',
            confirmText: 'ĐỒNG Ý',
            cancelText: 'HỦY',
            showCancel: true,
            onConfirm: () => logout(),
            onCancel: () => { }
        })
    };

    const MenuItem = ({ icon, color, title, subtitle, onPress, hasSwitch }) => (
        <TouchableOpacity
            style={styles.menuItem}
            onPress={onPress}
            disabled={hasSwitch}
        >
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <View style={[styles.menuIconBox, { backgroundColor: color + '15' }]}>
                    <MaterialCommunityIcons name={icon} size={22} color={color} />
                </View>
                <View>
                    <Text style={styles.menuText}>{title}</Text>
                    {subtitle && <Text style={{ fontSize: 12, color: '#95969D' }}>{subtitle}</Text>}
                </View>
            </View>

            {hasSwitch ? (
                <Switch
                    value={isNotiEnabled}
                    onValueChange={setIsNotiEnabled}
                    trackColor={{ false: "#767577", true: "#130160" }}
                    thumbColor={isNotiEnabled ? "white" : "#f4f3f4"}
                />
            ) : (
                <MaterialCommunityIcons name="chevron-right" size={24} color="#AAA6B9" />
            )}
        </TouchableOpacity>
    );

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: '#F5F7FA' }} edges={['top']}>
            <ScrollView showsVerticalScrollIndicator={false}>

                {/* 1. ẢNH BÌA & HEADER */}
                <Image
                    source={{ uri: 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1000&q=80' }}
                    style={styles.profileBanner}
                    resizeMode="cover"
                />

                <View style={styles.profileHeaderContainer}>
                    <Image
                        source={{ uri: user?.avatar || 'https://ui-avatars.com/api/?name=Ph%E1%BA%A1m%20John&background=random&color=fff&size=512&font-size=0.5' }}
                        style={styles.employerLogo}
                    />
                    <Text style={styles.companyName}>{profile?.company_name || '...Đang cập nhật'}</Text>
                    <Text style={styles.companyEmail}>{user?.email || '...Đang cập nhật'}</Text>

                    {/* Verify Badge */}
                    {profile?.is_verified && (
                        <View style={styles.verifyBadge}>
                            <MaterialCommunityIcons name="check-decagram" size={16} color="#00C566" />
                            <Text style={styles.verifyText}>Đã xác thực</Text>
                        </View>
                    )}
                </View>

                {/* 2. THỐNG KÊ NHANH */}
                <View style={styles.statsRow}>
                    <View style={styles.statItem}>
                        <Text style={styles.statNumber}>12</Text>
                        <Text style={styles.statLabel}>Tin đăng</Text>
                    </View>
                    <View style={styles.verticalDivider} />
                    <View style={styles.statItem}>
                        <Text style={styles.statNumber}>48</Text>
                        <Text style={styles.statLabel}>Ứng viên</Text>
                    </View>
                    <View style={styles.verticalDivider} />
                    <View style={styles.statItem}>
                        <Text style={styles.statNumber}>1.2k</Text>
                        <Text style={styles.statLabel}>Lượt xem</Text>
                    </View>
                </View>

                {/* 3. MENU CÔNG TY */}
                <Text style={{ marginLeft: 20, marginBottom: 10, fontSize: 16, fontWeight: 'bold', color: '#130160' }}>
                    Thông tin công ty
                </Text>
                <View style={styles.menuSection}>
                    <MenuItem
                        icon="pencil-outline" color="#2E5CFF" title="Chỉnh sửa hồ sơ"
                        subtitle="Cập nhật logo, địa chỉ, website"
                        onPress={() => navigation.navigate('EmployerEditProfile')}
                    />
                    <MenuItem
                        icon="image-multiple-outline" color="#FF9228" title="Thư viện ảnh"
                        subtitle="Quản lý ảnh văn phòng, hoạt động"
                        onPress={() => { }}
                    />
                </View>

                {/* 4. MENU CÀI ĐẶT */}
                <Text style={{ marginLeft: 20, marginBottom: 10, fontSize: 16, fontWeight: 'bold', color: '#130160' }}>
                    Cài đặt chung
                </Text>
                <View style={styles.menuSection}>
                    <MenuItem
                        icon="bell-outline" color="#00C566" title="Thông báo"
                        hasSwitch={true}
                    />
                    <MenuItem
                        icon="earth" color="#7B61FF" title="Ngôn ngữ"
                        subtitle="Tiếng Việt"
                        onPress={() => { }}
                    />
                    <MenuItem
                        icon="lock-outline" color="#FF4D4D" title="Đổi mật khẩu"
                        onPress={() => { }}
                    />
                </View>

                {/* 5. LOGOUT */}
                <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
                    <MaterialCommunityIcons name="logout" size={24} color="#FF4D4D" />
                    <Text style={styles.logoutText}>Đăng xuất</Text>
                </TouchableOpacity>

                <Text style={{ textAlign: 'center', color: '#AAA', marginBottom: 20 }}>
                    JobLink App Version 1.0.0
                </Text>

            </ScrollView>
        </SafeAreaView>
    );
};

export default EmployerProfile;