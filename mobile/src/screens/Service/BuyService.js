import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, FlatList, Alert, Image, ScrollView, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import Apis, { authApis, endpoints } from '../../utils/Apis';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Linking from 'expo-linking';
import { useDialog } from '../../hooks/useDialog';

// Logo ví dụ (Bạn có thể thay bằng ảnh trong assets của dự án)
const LOGO_VNPAY = "https://sandbox.vnpayment.vn/paymentv2/images/bank/ncb_logo.png";
const LOGO_CASH = "https://cdn-icons-png.flaticon.com/512/2489/2489756.png";

const BuyService = ({ route, navigation }) => {
    const { job } = route.params;
    const [packs, setPacks] = useState([]);
    const [selectedPack, setSelectedPack] = useState(null);
    const [paymentMethod, setPaymentMethod] = useState('VNPAY');
    const [loading, setLoading] = useState(false);
    const { showDialog } = useDialog();
    // --- Logic Deep Link (Giữ nguyên) ---
    useEffect(() => {
        const handleDeepLink = (event) => {
            console.log("Raw URL:", event.url);
            let data = Linking.parse(event.url);
            console.log("Parsed Data:", JSON.stringify(data, null, 2));
            const pathToCheck = data.path || data.hostname;
            if (pathToCheck?.includes('payment-result')) {
                const status = data.queryParams?.status;
                const order_id = data.queryParams?.order_id;
                const transaction_status = data.queryParams?.transaction_status;
                const transaction_info = data.queryParams?.transaction_info;
                console.log("✅ Đã phát hiện kết quả thanh toán. Đang điều hướng...");
                setTimeout(() => {
                    showDialog({
                        type: status,
                        title: transaction_status,
                        content: transaction_info
                    });
                    navigation.navigate('EmployerMain');
                }, 1000);
            }
        };

        const subscription = Linking.addEventListener('url', handleDeepLink);

        Linking.getInitialURL().then((url) => {
            if (url) handleDeepLink({ url });
        });

        return () => {
            subscription.remove();
        };
    }, []);

    // --- Load Packs ---
    useEffect(() => {
        const loadPacks = async () => {
            try {
                let res = await Apis.get(endpoints['service_packs']);
                const data = res.data.results || res.data;
                setPacks(data);
                // Tự động chọn gói đầu tiên
                if (data.length > 0) setSelectedPack(data[0]);
            } catch (error) {
                console.error(error);
            }
        };
        loadPacks();
    }, []);

    // --- Handle Payment ---
    const handlePayment = async () => {
        if (!selectedPack) {
            Alert.alert("Lỗi", "Vui lòng chọn gói dịch vụ");
            return;
        }

        setLoading(true);
        try {
            const token = await AsyncStorage.getItem('token');
            const payload = {
                pack_id: selectedPack.id,
                job_id: job.id,
                method: paymentMethod
            };

            // Nếu là VNPAY thì gọi API lấy link
            if (paymentMethod === 'VNPAY') {
                let res = await authApis(token).post(endpoints['create_payment'], payload);
                if (res.data.payment_url) {
                    Linking.openURL(res.data.payment_url);
                }
            }
            // Nếu là Tiền mặt hoặc phương thức khác xử lý ngay
            else {
                // Giả lập xử lý backend
                Alert.alert("Thông báo", "Vui lòng liên hệ admin để thanh toán tiền mặt.");
            }
        }
        catch (err) {
            console.error(err);
            Alert.alert("Lỗi", "Giao dịch thất bại");
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount) => {
        return parseInt(amount).toLocaleString('vi-VN') + ' đ';
    }

    // --- Render Items ---

    const renderPackItem = ({ item }) => {
        const isSelected = selectedPack?.id === item.id;
        return (
            <TouchableOpacity
                style={[styles.packCard, isSelected && styles.selectedPackCard]}
                onPress={() => setSelectedPack(item)}
                activeOpacity={0.8}
            >
                <View style={styles.packHeader}>
                    <View style={styles.radioContainer}>
                        <View style={[styles.radioOuter, isSelected && { borderColor: '#FF9228' }]}>
                            {isSelected && <View style={styles.radioInner} />}
                        </View>
                    </View>
                    <View style={{ flex: 1, marginLeft: 10 }}>
                        <Text style={[styles.packName, isSelected && { color: '#FF9228' }]}>{item.name}</Text>
                        <Text style={styles.packDuration}>Thời hạn: {item.duration_days} ngày</Text>
                    </View>
                    <Text style={[styles.packPrice, isSelected && { color: '#FF9228' }]}>
                        {formatCurrency(item.price)}
                    </Text>
                </View>
                {/* Nếu có mô tả gói thì hiện ở đây */}
                {item.description ? (
                    <Text style={styles.packDesc}>{item.description}</Text>
                ) : null}
            </TouchableOpacity>
        );
    };

    const renderPaymentMethod = (key, name, iconUrl, subtitle) => {
        const isSelected = paymentMethod === key;
        return (
            <TouchableOpacity
                style={[styles.methodCard, isSelected && styles.selectedMethodCard]}
                onPress={() => setPaymentMethod(key)}
            >
                <Image source={{ uri: iconUrl }} style={styles.methodIcon} resizeMode="contain" />
                <View style={{ flex: 1 }}>
                    <Text style={styles.methodName}>{name}</Text>
                    {subtitle && <Text style={styles.methodSubtitle}>{subtitle}</Text>}
                </View>
                {isSelected && (
                    <MaterialCommunityIcons name="check-circle" size={24} color="#FF9228" />
                )}
            </TouchableOpacity>
        );
    }

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            {/* HEADER */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
                    <MaterialCommunityIcons name="arrow-left" size={24} color="#130160" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Thanh toán dịch vụ</Text>
                <View style={{ width: 24 }} />
            </View>

            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>

                {/* 1. INFO JOB */}
                <View style={styles.section}>
                    <Text style={styles.sectionLabel}>Tin tuyển dụng:</Text>
                    <View style={styles.jobInfoCard}>
                        <View style={styles.iconBox}>
                            <MaterialCommunityIcons name="briefcase-variant" size={24} color="#FFF" />
                        </View>
                        <View style={{ flex: 1 }}>
                            <Text style={styles.jobTitle} numberOfLines={2}>{job?.title}</Text>
                            <Text style={styles.jobId}>Mã tin: #{job?.id}</Text>
                        </View>
                    </View>
                </View>

                {/* 2. CHỌN GÓI */}
                <View style={styles.section}>
                    <Text style={styles.sectionLabel}>Chọn gói dịch vụ:</Text>
                    <FlatList
                        data={packs}
                        keyExtractor={item => item.id.toString()}
                        renderItem={renderPackItem}
                        scrollEnabled={false} // Tắt scroll của flatlist lồng
                    />
                </View>

                {/* 3. PHƯƠNG THỨC THANH TOÁN */}
                <View style={styles.section}>
                    <Text style={styles.sectionLabel}>Phương thức thanh toán:</Text>

                    {renderPaymentMethod(
                        'VNPAY',
                        'VNPAY / Thẻ ngân hàng',
                        LOGO_VNPAY,
                        'Thanh toán nhanh qua ứng dụng ngân hàng'
                    )}

                    {renderPaymentMethod(
                        'CASH',
                        'Tiền mặt',
                        LOGO_CASH,
                        'Liên hệ nhân viên để thanh toán trực tiếp'
                    )}
                </View>

                {/* 4. SUMMARY */}
                <View style={styles.summarySection}>
                    <View style={styles.rowBetween}>
                        <Text style={styles.sumText}>Tạm tính</Text>
                        <Text style={styles.sumVal}>{selectedPack ? formatCurrency(selectedPack.price) : '0 đ'}</Text>
                    </View>
                    <View style={[styles.rowBetween, { marginTop: 8 }]}>
                        <Text style={styles.sumText}>Giảm giá</Text>
                        <Text style={[styles.sumVal, { color: '#28a745' }]}>- 0 đ</Text>
                    </View>
                    <View style={styles.divider} />
                    <View style={styles.rowBetween}>
                        <Text style={styles.totalLabel}>Tổng thanh toán</Text>
                        <Text style={styles.totalVal}>{selectedPack ? formatCurrency(selectedPack.price) : '0 đ'}</Text>
                    </View>
                </View>

                {/* Padding bottom để không bị che bởi nút */}
                <View style={{ height: 20 }} />

            </ScrollView>

            {/* BOTTOM BUTTON */}
            <View style={styles.footer}>
                <TouchableOpacity
                    style={[styles.payBtn, loading && { opacity: 0.7 }]}
                    onPress={handlePayment}
                    disabled={loading}
                >
                    {loading ? (
                        <Text style={styles.payBtnText}>Đang xử lý...</Text>
                    ) : (
                        <Text style={styles.payBtnText}>
                            THANH TOÁN • {selectedPack ? formatCurrency(selectedPack.price) : '0 đ'}
                        </Text>
                    )}
                </TouchableOpacity>
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#F9F9F9' },

    // Header
    header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 15, backgroundColor: '#FFF' },
    backBtn: { padding: 5 },
    headerTitle: { fontSize: 18, fontWeight: 'bold', color: '#130160' },

    scrollContent: { padding: 20 },

    // Sections
    section: { marginBottom: 25 },
    sectionLabel: { fontSize: 16, fontWeight: 'bold', color: '#130160', marginBottom: 10 },

    // Job Info
    jobInfoCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF', padding: 15, borderRadius: 12, elevation: 2 },
    iconBox: { width: 45, height: 45, borderRadius: 10, backgroundColor: '#130160', alignItems: 'center', justifyContent: 'center', marginRight: 15 },
    jobTitle: { fontSize: 16, fontWeight: '600', color: '#333' },
    jobId: { fontSize: 13, color: '#888', marginTop: 4 },

    // Pack Cards
    packCard: { backgroundColor: '#FFF', borderRadius: 12, padding: 15, marginBottom: 10, borderWidth: 1, borderColor: '#EEE' },
    selectedPackCard: { borderColor: '#FF9228', backgroundColor: '#FFF8F0' },
    packHeader: { flexDirection: 'row', alignItems: 'center' },
    packName: { fontSize: 15, fontWeight: 'bold', color: '#333' },
    packDuration: { fontSize: 12, color: '#666', marginTop: 2 },
    packPrice: { fontSize: 15, fontWeight: 'bold', color: '#130160' },
    packDesc: { fontSize: 13, color: '#666', marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#EEE' },

    // Radio Custom
    radioContainer: { justifyContent: 'center', alignItems: 'center' },
    radioOuter: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, borderColor: '#CCC', justifyContent: 'center', alignItems: 'center' },
    radioInner: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#FF9228' },

    // Payment Methods
    methodCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFF', padding: 15, borderRadius: 12, marginBottom: 10, borderWidth: 1, borderColor: '#EEE' },
    selectedMethodCard: { borderColor: '#FF9228', backgroundColor: '#FFF8F0' },
    methodIcon: { width: 40, height: 40, marginRight: 15 },
    methodName: { fontSize: 15, fontWeight: 'bold', color: '#333' },
    methodSubtitle: { fontSize: 12, color: '#888', marginTop: 2 },

    // Summary
    summarySection: { backgroundColor: '#FFF', padding: 20, borderRadius: 12 },
    rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    sumText: { fontSize: 14, color: '#666' },
    sumVal: { fontSize: 14, fontWeight: '600', color: '#333' },
    divider: { height: 1, backgroundColor: '#EEE', marginVertical: 15 },
    totalLabel: { fontSize: 16, fontWeight: 'bold', color: '#130160' },
    totalVal: { fontSize: 18, fontWeight: 'bold', color: '#FF9228' },

    // Footer
    footer: { padding: 20, backgroundColor: '#FFF', borderTopWidth: 1, borderTopColor: '#EEE' },
    payBtn: { backgroundColor: '#130160', paddingVertical: 16, borderRadius: 30, alignItems: 'center', shadowColor: "#130160", shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 4.65, elevation: 8 },
    payBtnText: { color: '#FFF', fontSize: 16, fontWeight: 'bold' },
});

export default BuyService;