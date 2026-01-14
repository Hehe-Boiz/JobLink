import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, FlatList, Alert, Linking } from 'react-native';
import { RadioButton, Button, Card } from 'react-native-paper';
import Apis, { authApis, endpoints } from '../../utils/Apis';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BuyService = ({ route, navigation }) => {
    const { job } = route.params;
    const [packs, setPacks] = useState([]);
    const [selectedPack, setSelectedPack] = useState(null);
    const [paymentMethod, setPaymentMethod] = useState('MOMO');
    const [loading, setLoading] = useState(false);
    useEffect(() => {
        // Hàm xử lý khi App được mở từ Deep Link
        const handleDeepLink = (event) => {
            let data = Linking.parse(event.url);
            
            // data.path sẽ là 'payment-result'
            // data.queryParams sẽ là { status: 'success', order_id: '...' }
            
            if (data.path === 'payment-result') {
                if (data.queryParams.status === 'success') {
                    Alert.alert("Thành công", "Thanh toán VNPAY thành công!");
                    navigation.goBack(); // Quay về
                } else {
                    Alert.alert("Thất bại", "Thanh toán bị lỗi hoặc bị hủy.");
                }
            }
        };

        // 1. Lắng nghe khi App đang chạy ngầm (Background)
        const subscription = Linking.addEventListener('url', handleDeepLink);

        // 2. Kiểm tra nếu App đang tắt hẳn mà được bật lên (Cold Start)
        Linking.getInitialURL().then((url) => {
            if (url) handleDeepLink({ url });
        });

        return () => {
            subscription.remove();
        };
    }, []);
    useEffect(() => {
        const loadPacks = async () => {
            let res = await Apis.get(endpoints['service_packs']);
            setPacks(res.data.results || res.data);
        };
        loadPacks();
    }, []);

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

            if (paymentMethod === 'MOMO' || paymentMethod === 'VNPAY') {
                let res = await authApis(token).post(endpoints['create_payment'], payload);

                if (res.data.payment_url) {
                    // Mở app MoMo hoặc Trình duyệt để thanh toán
                    Linking.openURL(res.data.payment_url);

                    // Sau khi mở, bạn có thể hiện một cái Modal hỏi người dùng
                    // "Bạn đã thanh toán xong chưa?" -> Nếu bấm "Rồi" thì gọi API kiểm tra lại trạng thái
                    Alert.alert(
                        "Đang thanh toán",
                        "Vui lòng hoàn tất thanh toán trên trình duyệt",
                        [
                            { text: "Tôi đã thanh toán xong", onPress: () => navigation.goBack() },
                            { text: "Để sau" }
                        ]
                    );
                }
            }
        }
        catch (err) {
            console.error(err);
            Alert.alert("Lỗi", "Giao dịch thất bại");
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={{ flex: 1, padding: 20, backgroundColor: '#fff' }}>
            <Text style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 15 }}>Nâng cấp tin: {job.title}</Text>

            <Text style={{ fontWeight: 'bold' }}>1. Chọn gói dịch vụ:</Text>
            <FlatList
                data={packs}
                keyExtractor={item => item.id.toString()}
                renderItem={({ item }) => (
                    <TouchableOpacity onPress={() => setSelectedPack(item)}>
                        <Card style={{ marginVertical: 5, backgroundColor: selectedPack?.id === item.id ? '#e3f2fd' : '#fff' }}>
                            <Card.Content>
                                <Text style={{ fontWeight: 'bold' }}>{item.name}</Text>
                                <Text>{parseInt(item.price).toLocaleString()} VNĐ / {item.duration_days} ngày</Text>
                            </Card.Content>
                        </Card>
                    </TouchableOpacity>
                )}
            />

            <Text style={{ fontWeight: 'bold', marginTop: 20 }}>2. Phương thức thanh toán:</Text>
            <RadioButton.Group onValueChange={setPaymentMethod} value={paymentMethod}>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <RadioButton value="MOMO" />
                    <Text>Ví MoMo</Text>
                </View>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <RadioButton value="ZALOPAY" />
                    <Text>ZaloPay</Text>
                </View>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <RadioButton value="STRIPE" />
                    <Text>Thẻ Quốc tế (Visa/Master)</Text>
                </View>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <RadioButton value="VNPAY" />
                    <Text>VNPAY / Thẻ ATM</Text>
                </View>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <RadioButton value="CASH" />
                    <Text>Tiền mặt</Text>
                </View>
            </RadioButton.Group>

            <Button mode="contained" onPress={handlePayment} loading={loading} style={{ marginTop: 30, backgroundColor: '#130160' }}>
                THANH TOÁN {selectedPack ? parseInt(selectedPack.price).toLocaleString() : '0'} VNĐ
            </Button>
        </View>
    );
}
export default BuyService;