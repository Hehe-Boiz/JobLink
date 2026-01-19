import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { Button } from 'react-native-paper';

const PaymentResult = ({ route, navigation }) => {
    const { status, order_id, user_role } = route.params || {};

    const isSuccess = status === 'success';
    console.log(user_role);
    return (
        <View style={styles.container}>
            <View style={styles.content}>
                {/* Icon Check xanh hoặc X đỏ */}
                <Text style={{ fontSize: 80, marginBottom: 20 }}>
                    {isSuccess ? "🎉" : "⚠️"}
                </Text>

                <Text style={[styles.title, { color: isSuccess ? '#28a745' : '#dc3545' }]}>
                    {isSuccess ? 'THANH TOÁN THÀNH CÔNG!' : 'GIAO DỊCH THẤT BẠI'}
                </Text>

                <Text style={styles.message}>
                    {isSuccess 
                        ? 'Cảm ơn bạn đã sử dụng dịch vụ. Gói tin của bạn đã được kích hoạt.' 
                        : 'Có lỗi xảy ra trong quá trình thanh toán hoặc bạn đã hủy giao dịch.'}
                </Text>

                <View style={styles.infoBox}>
                    <Text style={styles.infoLabel}>Mã giao dịch:</Text>
                    <Text style={styles.infoValue}>{order_id}</Text>
                </View>

                <Button 
                    mode="contained" 
                    onPress={() => navigation.navigate('EmployerMain')}
                    style={{ marginTop: 30, backgroundColor: '#130160' }}
                >
                    VỀ TRANG CHỦ
                </Button>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#fff', justifyContent: 'center', padding: 20 },
    content: { alignItems: 'center' },
    title: { fontSize: 24, fontWeight: 'bold', marginBottom: 10, textAlign: 'center' },
    message: { fontSize: 16, color: '#666', textAlign: 'center', marginBottom: 30 },
    infoBox: { padding: 15, backgroundColor: '#f5f5f5', borderRadius: 8, width: '100%', alignItems: 'center' },
    infoLabel: { fontSize: 14, color: '#888' },
    infoValue: { fontSize: 16, fontWeight: 'bold', marginTop: 5 }
});

export default PaymentResult;