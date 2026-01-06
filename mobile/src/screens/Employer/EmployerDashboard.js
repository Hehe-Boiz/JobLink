import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Dimensions } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { LineChart, BarChart, PieChart } from 'react-native-chart-kit';
import { Menu } from 'react-native-paper'; // Dùng lại Dropdown cũ của bạn
import styles from '../../styles/Employer/EmployerStyles';

const screenWidth = Dimensions.get('window').width;

const EmployerDashboard = () => {
  const [filter, setFilter] = useState('Tháng');
  const [visible, setVisible] = useState(false); // Cho dropdown menu

  // Data mẫu
  const lineData = {
    labels: ["T1", "T2", "T3", "T4", "T5", "T6"],
    datasets: [
      { data: [20, 45, 28, 80, 99, 43], color: (opacity = 1) => `rgba(46, 92, 255, ${opacity})`, strokeWidth: 2 }, // Xanh
      { data: [10, 20, 50, 40, 60, 70], color: (opacity = 1) => `rgba(0, 197, 102, ${opacity})`, strokeWidth: 2 } // Xanh lá
    ],
    legend: ["Đơn ứng tuyển", "Lượt xem"]
  };

  const pieData = [
    { name: "IT", population: 35, color: "#2E5CFF", legendFontColor: "#7F7F7F", legendFontSize: 12 },
    { name: "Sales", population: 15, color: "#FF4D4D", legendFontColor: "#7F7F7F", legendFontSize: 12 },
    { name: "Marketing", population: 25, color: "#00C566", legendFontColor: "#7F7F7F", legendFontSize: 12 },
    { name: "Design", population: 20, color: "#FF9228", legendFontColor: "#7F7F7F", legendFontSize: 12 },
  ];

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      
      {/* 1. Header Xanh */}
      <View style={styles.blueHeader}>
        <Text style={styles.headerTitleWhite}>Dashboard Tổng Quan</Text>
        <Text style={styles.headerSubWhite}>Hôm nay bạn có 3 đơn ứng tuyển mới</Text>
        
        {/* Filter Tabs (Giữ nguyên logic dropdown của bạn nếu muốn, hoặc dùng UI Tab này) */}
        <View style={styles.filterContainer}>
            {['Tháng', 'Quý', 'Năm'].map((item) => (
                <TouchableOpacity 
                    key={item} 
                    style={[styles.filterItem, filter === item && styles.filterActive]}
                    onPress={() => setFilter(item)}
                >
                    <Text style={[styles.filterText, filter === item && styles.filterTextActive]}>{item}</Text>
                </TouchableOpacity>
            ))}
        </View>
      </View>

      {/* 2. 4 Cards Thống kê */}
      <View style={styles.gridContainer}>
          <StatsCard icon="file-document" color="#2E5CFF" label="Tin tuyển dụng" value="12" trend="+3" />
          <StatsCard icon="account-group" color="#00C566" label="Ứng viên mới" value="48" trend="+12" />
          <StatsCard icon="eye" color="#A020F0" label="Lượt xem" value="1,247" trend="+156" />
          <StatsCard icon="chart-line" color="#FF9228" label="Tăng trưởng" value="23%" trend="+5%" />
      </View>

      <View style={{ height: 20 }} />

      {/* 3. Biểu đồ Xu hướng (Line) */}
      <View style={styles.chartCard}>
        <Text style={styles.chartTitle}>Xu hướng ứng tuyển & lượt xem</Text>
        <LineChart
            data={lineData}
            width={screenWidth - 60}
            height={220}
            chartConfig={{
                backgroundGradientFrom: "#fff", backgroundGradientTo: "#fff",
                color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                decimalPlaces: 0,
            }}
            bezier
            style={{ borderRadius: 16 }}
        />
      </View>

      {/* 4. Biểu đồ Phân bổ (Pie) */}
      <View style={styles.chartCard}>
        <Text style={styles.chartTitle}>Phân bổ vị trí tuyển dụng</Text>
        <PieChart
            data={pieData}
            width={screenWidth - 60}
            height={200}
            chartConfig={{ color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})` }}
            accessor={"population"}
            backgroundColor={"transparent"}
            paddingLeft={"15"}
            absolute
        />
      </View>

    </ScrollView>
  );
};

// Component con cho Card nhỏ
const StatsCard = ({ icon, color, label, value, trend }) => (
    <View style={styles.statCard}>
        <View style={styles.rowBetween}>
            <Text style={styles.statLabel}>{label}</Text>
            <MaterialCommunityIcons name={icon} size={20} color={color} />
        </View>
        <Text style={styles.statValue}>{value}</Text>
        <Text style={[styles.statTrend, { color: color }]}>↗ {trend}</Text>
    </View>
);

export default EmployerDashboard;