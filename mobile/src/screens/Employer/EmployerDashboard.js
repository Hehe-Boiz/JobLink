import React, { useContext, useState, useEffect, useCallback } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Image, Dimensions, StatusBar, ActivityIndicator } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LineChart } from 'react-native-chart-kit'; // Dùng Chart Kit
import { useFocusEffect } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import styles from '../../styles/Employer/EmployerStyles';
import { MyUserContext } from '../../utils/contexts/MyContext';
import { authApis } from '../../utils/Apis';
import StatCard from '../../components/Employer/StatCard';

const screenWidth = Dimensions.get('window').width;

const EmployerDashboard = ({ navigation }) => {
    const [user] = useContext(MyUserContext);
    const [loading, setLoading] = useState(false);
    
    const [period, setPeriod] = useState('month');
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

    const [chartData, setChartData] = useState({ 
        labels: ["T1", "T2"], 
        datasets: [{ data: [0, 0] }] 
    });
    const [categories, setCategories] = useState([]);

    const currentYear = new Date().getFullYear();
    const yearsList = [currentYear - 2, currentYear - 1, currentYear, currentYear + 1, currentYear + 2];

    const loadStats = async () => {
        try {
            
            const token = await AsyncStorage.getItem('token');
            const url = `/employer-stats/?period=${period}&category_id=${selectedCategory}&year=${selectedYear}`;
            console.log("Fetching:", url);
            
            const res = await authApis(token).get(url);
            
            if (res.data.categories) {
                setCategories([{id: 'all', name: 'Tất cả ngành'}, ...res.data.categories]);
            }

            if (res.data.chart_data) {
                setChartData({
                    labels: res.data.chart_data.labels,
                    datasets: [{
                        data: res.data.chart_data.data.length > 0 ? res.data.chart_data.data : [0],
                        color: (opacity = 1) => `rgba(255, 146, 40, ${opacity})`,
                        strokeWidth: 3
                    }],
                    legend: ["Hiệu quả tuyển dụng (%)"]
                });
            }
        } catch (err) {
            console.error("Lỗi tải dashboard:", err);
        } finally {
            setLoading(false);
        }
    };

    useFocusEffect(
        useCallback(() => {
            loadStats();
        }, [period, selectedCategory, selectedYear])
    );


    const chartConfig = {
        backgroundGradientFrom: "#FFFFFF",
        backgroundGradientTo: "#FFFFFF",
        color: (opacity = 1) => `rgba(19, 1, 96, ${opacity})`,
        strokeWidth: 2,
        barPercentage: 0.5,
        decimalPlaces: 1,
        propsForDots: { r: "4", strokeWidth: "2", stroke: "#FF9228" }, // Dot cam
        fillShadowGradientFrom: "#FF9228",
        fillShadowGradientTo: "#FFFFFF",
        fillShadowGradientOpacity: 0.3,
    };

    return (
        <View style={{ flex: 1, backgroundColor: '#F5F7FA' }}>
            <StatusBar barStyle="light-content" backgroundColor="#130160" />
            
            {/* HEADER */}
            <View style={styles.proHeader}>
                <View style={styles.headerLeft}>
                    <Text style={styles.dateText}>DASHBOARD</Text>
                    <Text style={styles.welcomeText}>Báo cáo hiệu quả 📊</Text>
                </View>
                <TouchableOpacity style={styles.avatarContainer} onPress={() => navigation.navigate('EmployerProfile')}>
                    <Image source={{ uri: user?.avatar }} style={styles.headerAvatar} />
                </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false} style={{ flex: 1 }}>
                <View style={styles.statsContainerPro}>
                    <StatCard icon="file-document-outline" color="#2E5CFF" bg="#E6E1FF" value="12" label="Tin đang đăng" />
                    <StatCard icon="account-group-outline" color="#FF9228" bg="#FFF4E5" value="38" label="Hồ sơ mới" />
                </View>

                {/* 1. LỌC NGÀNH NGHỀ */}
                <View style={{ marginTop: 10,paddingHorizontal: 20 }}>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                        {categories.map((cat) => (
                            <TouchableOpacity
                                key={cat.id}
                                onPress={() => setSelectedCategory(cat.id)}
                                style={{
                                    backgroundColor: selectedCategory === cat.id ? '#FF9228' : 'white',
                                    paddingHorizontal: 15, paddingVertical: 8,
                                    borderRadius: 20, marginRight: 10,
                                    elevation: 0
                                }}
                            >
                                <Text style={{ 
                                    color: selectedCategory === cat.id ? 'white' : '#524B6B',
                                    fontWeight: 'bold', fontSize: 13
                                }}>
                                    {cat.name}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </ScrollView>
                </View>

                {/* 2. KHUNG BIỂU ĐỒ */}
                <View style={{ marginTop: 20, marginHorizontal: 20 }}>
                    <View style={{ backgroundColor: 'white', borderRadius: 20, padding: 15, elevation: 4 }}>
                        
                        <Text style={{ fontSize: 16, fontWeight: 'bold', color: '#130160', marginBottom: 10 }}>
                            Tỷ lệ chuyển đổi (App/View)
                        </Text>

                        {/* Chart */}
                        <LineChart
                            data={chartData}
                            width={screenWidth - 70}
                            height={220}
                            chartConfig={chartConfig}
                            bezier
                            style={{ marginVertical: 8, borderRadius: 16 }}
                            yAxisSuffix="%"
                            fromZero
                            withInnerLines={true}
                            withOuterLines={false}
                        />

                        {/* 3. BỘ LỌC THỜI GIAN */}
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 15 }}>
                            {/* Cột trái: Chọn Loại (Tháng/Quý/Năm) */}
                            <View style={{ flexDirection: 'row', backgroundColor: '#F5F7FA', borderRadius: 10, padding: 3 }}>
                                <FilterBtn title="Tháng" active={period === 'month'} onPress={() => setPeriod('month')} />
                                <FilterBtn title="Quý" active={period === 'quarter'} onPress={() => setPeriod('quarter')} />
                                <FilterBtn title="Năm" active={period === 'year'} onPress={() => setPeriod('year')} />
                            </View>

                            {/* Cột phải: Chọn Năm (Chỉ hiện khi không phải mode Year) */}
                            {period !== 'year' && (
                                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                    <MaterialCommunityIcons name="calendar-month" size={20} color="#95969D" style={{marginRight: 5}}/>
                                    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ maxWidth: 100 }}>
                                        {yearsList.map(y => (
                                            <TouchableOpacity 
                                                key={y} 
                                                onPress={() => setSelectedYear(y)}
                                                style={{ 
                                                    paddingHorizontal: 8, paddingVertical: 4, 
                                                    backgroundColor: selectedYear === y ? '#130160' : 'transparent',
                                                    borderRadius: 6, marginRight: 4
                                                }}
                                            >
                                                <Text style={{ 
                                                    color: selectedYear === y ? 'white' : '#524B6B', 
                                                    fontWeight: 'bold', fontSize: 12 
                                                }}>{y}</Text>
                                            </TouchableOpacity>
                                        ))}
                                    </ScrollView>
                                </View>
                            )}
                        </View>

                    </View>
                </View>

                {/* 4. CHÚ THÍCH */}
                <View style={{ padding: 20 }}>
                    <Text style={{color: '#95969D', textAlign: 'center', fontSize: 12}}>
                        Biểu đồ thể hiện tỷ lệ % số người nộp đơn so với số người xem tin tuyển dụng
                    </Text>
                </View>
                
                <View style={{height: 30}} />
            </ScrollView>
        </View>
    );
};

// Component Button Lọc
const FilterBtn = ({ title, active, onPress }) => (
    <TouchableOpacity 
        onPress={onPress}
        style={{ 
            paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8,
            backgroundColor: active ? '#130160' : 'transparent'
        }}
    >
        <Text style={{ fontSize: 12, fontWeight: '600', color: active ? 'white' : '#95969D' }}>
            {title}
        </Text>
    </TouchableOpacity>
);

export default EmployerDashboard;