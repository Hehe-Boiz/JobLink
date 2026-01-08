import React, { useContext, useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Image, Dimensions, StatusBar } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LineChart, PieChart, BarChart } from 'react-native-chart-kit'; // Thêm PieChart, BarChart
import styles from '../../styles/Employer/EmployerStyles';
import { MyUserContext } from '../../utils/contexts/MyContext';

const screenWidth = Dimensions.get('window').width;

const EmployerDashboard = ({ navigation }) => {
    const [user] = useContext(MyUserContext);
    const [currentDate, setCurrentDate] = useState('');
    
    // State quản lý Filter
    const [timeFilter, setTimeFilter] = useState('month'); // 'week' | 'month' | 'year'

    useEffect(() => {
        const date = new Date();
        setCurrentDate(date.toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long' }));
    }, []);

    // --- MOCK DATA THEO FILTER ---
    // 1. Data cho Line Chart (Xu hướng ứng tuyển)
    const getLineData = () => {
        switch (timeFilter) {
            case 'week': return { labels: ["T2", "T3", "T4", "T5", "T6", "T7", "CN"], data: [5, 12, 8, 20, 15, 10, 25] };
            case 'year': return { labels: ["Q1", "Q2", "Q3", "Q4"], data: [120, 250, 180, 300] };
            default: return { labels: ["Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4"], data: [45, 60, 30, 80] }; // Month
        }
    };

    // 2. Data cho Bar Chart (Hiệu quả tin đăng: View vs Apply)
    const barData = {
        labels: ["IT", "MKT", "Sale", "HR"],
        datasets: [{ data: [500, 300, 200, 100] }] // Số liệu View
    };

    // 3. Data cho Pie Chart (Chất lượng ứng viên)
    const pieData = [
        { name: "Chờ duyệt", population: 15, color: "#FF9228", legendFontColor: "#7F7F7F", legendFontSize: 12 },
        { name: "Phỏng vấn", population: 8, color: "#2E5CFF", legendFontColor: "#7F7F7F", legendFontSize: 12 },
        { name: "Đạt", population: 5, color: "#00C566", legendFontColor: "#7F7F7F", legendFontSize: 12 },
        { name: "Loại", population: 10, color: "#FF4D4D", legendFontColor: "#7F7F7F", legendFontSize: 12 }
    ];

    // Config chung cho Chart
    const chartConfig = {
        backgroundGradientFrom: "#FFFFFF",
        backgroundGradientTo: "#FFFFFF",
        color: (opacity = 1) => `rgba(19, 1, 96, ${opacity})`,
        strokeWidth: 2,
        barPercentage: 0.6,
        decimalPlaces: 0,
    };

    return (
        <View style={{ flex: 1, backgroundColor: '#F5F7FA' }}>
            <StatusBar barStyle="light-content" backgroundColor="#130160" />
            
            {/* 1. HEADER (Giữ nguyên) */}
            <View style={styles.proHeader}>
                <View style={styles.headerLeft}>
                    <Text style={styles.dateText}>{currentDate}</Text>
                    <Text style={styles.welcomeText}>Xin chào, {user?.last_name || "HR Manager"}</Text>
                </View>
                <View style={styles.headerRight}>
                    <TouchableOpacity style={styles.notifBtn}>
                        <MaterialCommunityIcons name="bell-outline" size={24} color="white" />
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.avatarContainer} onPress={() => navigation.navigate('EmployerProfile')}>
                        <Image source={{ uri: user?.avatar || 'https://ui-avatars.com/api/?name=HR' }} style={styles.headerAvatar} />
                    </TouchableOpacity>
                </View>
            </View>

            <ScrollView showsVerticalScrollIndicator={false} style={{ flex: 1 }}>
                
                {/* 2. STATS CARDS */}
                <View style={styles.statsContainerPro}>
                    <StatCard icon="file-document-outline" color="#2E5CFF" bg="#E6E1FF" value="12" label="Tin đang đăng" />
                    <StatCard icon="account-group-outline" color="#FF9228" bg="#FFF4E5" value="38" label="Hồ sơ mới" />
                </View>

                {/* 3. TIME FILTER TABS (MỚI) */}
                <View style={styles.filterTabContainer}>
                    <FilterTab title="Tuần này" active={timeFilter === 'week'} onPress={() => setTimeFilter('week')} />
                    <FilterTab title="Tháng này" active={timeFilter === 'month'} onPress={() => setTimeFilter('month')} />
                    <FilterTab title="Năm nay" active={timeFilter === 'year'} onPress={() => setTimeFilter('year')} />
                </View>

                {/* 4. BIỂU ĐỒ XU HƯỚNG (LINE CHART) */}
                <View style={styles.sectionHeaderPro}>
                    <Text style={styles.sectionTitlePro}>Xu hướng ứng tuyển</Text>
                </View>
                <View style={styles.chartCardPro}>
                    <LineChart
                        data={{
                            labels: getLineData().labels,
                            datasets: [{ data: getLineData().data }]
                        }}
                        width={screenWidth - 60}
                        height={220}
                        chartConfig={{
                            ...chartConfig,
                            color: (opacity = 1) => `rgba(46, 92, 255, ${opacity})`, // Màu xanh chủ đạo
                        }}
                        bezier
                        style={{ borderRadius: 16 }}
                        withVerticalLines={false}
                    />
                </View>

                {/* 5. BIỂU ĐỒ CHẤT LƯỢNG ỨNG VIÊN (PIE CHART - MỚI) */}
                <View style={styles.sectionHeaderPro}>
                    <Text style={styles.sectionTitlePro}>Phân loại hồ sơ</Text>
                </View>
                <View style={styles.chartCardPro}>
                    <PieChart
                        data={pieData}
                        width={screenWidth - 40}
                        height={200}
                        chartConfig={chartConfig}
                        accessor={"population"}
                        backgroundColor={"transparent"}
                        paddingLeft={"15"}
                        center={[10, 0]}
                        absolute
                    />
                </View>

                {/* 6. BIỂU ĐỒ HIỆU QUẢ TIN ĐĂNG (BAR CHART - MỚI) */}
                <View style={styles.sectionHeaderPro}>
                    <Text style={styles.sectionTitlePro}>Lượt xem theo ngành nghề</Text>
                </View>
                <View style={styles.chartCardPro}>
                    <BarChart
                        data={barData}
                        width={screenWidth - 60}
                        height={220}
                        yAxisLabel=""
                        chartConfig={{
                            ...chartConfig,
                            color: (opacity = 1) => `rgba(19, 1, 96, ${opacity})`, // Màu cột
                        }}
                        style={{ borderRadius: 16 }}
                        fromZero
                        showValuesOnTopOfBars // Hiển thị số trên cột
                    />
                </View>

                <View style={{height: 30}} />
            </ScrollView>
        </View>
    );
};

// --- SUB COMPONENTS ---

const StatCard = ({ icon, color, bg, value, label }) => (
    <TouchableOpacity style={styles.statCardPro} activeOpacity={0.9}>
        <View style={[styles.statIconBox, { backgroundColor: bg }]}>
            <MaterialCommunityIcons name={icon} size={24} color={color} />
        </View>
        <Text style={styles.statNumberPro}>{value}</Text>
        <Text style={styles.statLabelPro}>{label}</Text>
    </TouchableOpacity>
);

const FilterTab = ({ title, active, onPress }) => (
    <TouchableOpacity 
        style={[styles.filterTab, active && styles.filterTabActive]} 
        onPress={onPress}
    >
        <Text style={[styles.filterText, active && styles.filterTextActive]}>{title}</Text>
    </TouchableOpacity>
);

export default EmployerDashboard;