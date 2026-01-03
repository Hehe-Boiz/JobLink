import React from 'react';
import { View, ScrollView, StyleSheet, Image, TouchableOpacity } from 'react-native';
import { Text, Avatar, Searchbar, Card, Button, useTheme, IconButton, FAB } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import EmployerHomeStyles from '../../styles/Employer/EmployerHomeStyles';
import ApplicantCard from '../../components/Employer/ApplicationCard';
const EmployerHome = () => {
    const theme = useTheme();
    const [searchQuery, setSearchQuery] = React.useState('');

    // Mock Data: Ứng viên mới nhất (Giả lập cấu trúc giống Job Card trong hình)
    const recentApplicants = [
        {
            id: 1,
            name: 'Nguyen Van A',
            position: 'Product Designer',
            status: 'Chờ duyệt',
            salary_expect: '$1000',
            tags: ['Senior', 'Full Time'],
            avatar: 'https://i.pravatar.cc/150?u=1'
        },
        {
            id: 2,
            name: 'Le Thi B',
            position: 'React Native Dev',
            status: 'Đã xem',
            salary_expect: '$1500',
            tags: ['Mid', 'Remote'],
            avatar: 'https://i.pravatar.cc/150?u=2'
        },
    ];

    return (
        <View style={EmployerHomeStyles.container}>
            <ScrollView contentContainerStyle={{ paddingBottom: 80 }} showsVerticalScrollIndicator={false}>

                {/* 1. HEADER: Hello + Avatar */}
                <View style={EmployerHomeStyles.header}>
                    <View>
                        <Text variant="headlineSmall" style={{ fontWeight: 'bold', color: '#0D0D26' }}>Hello</Text>
                        <Text variant="headlineMedium" style={{ fontWeight: 'bold', color: '#0D0D26' }}>FPT Software.</Text>
                    </View>
                    <Avatar.Image size={50} source={{ uri: 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/FPT_logo_2010.svg/1200px-FPT_logo_2010.svg.png' }} style={{ backgroundColor: '#F5F5F5' }} />
                </View>

                {/* 2. SEARCH BAR (Giống hình 2) */}
                <Searchbar
                    placeholder="Search candidates..."
                    onChangeText={setSearchQuery}
                    value={searchQuery}
                    style={EmployerHomeStyles.searchBar}
                    inputStyle={{ minHeight: 0 }}
                    iconColor="#95969D"
                />

                {/* 3. BANNER (Màu xanh đậm + Nút Cam) */}
                <View style={EmployerHomeStyles.bannerContainer}>
                    <View style={EmployerHomeStyles.bannerContent}>
                        <Text style={EmployerHomeStyles.bannerTitle}>Find the best Talent today!</Text>
                        <Button
                            mode="contained"
                            buttonColor="#FFB224" // Màu cam giống hình
                            textColor="#0D0D26"
                            style={EmployerHomeStyles.bannerBtn}
                            labelStyle={{ fontWeight: 'bold' }}
                            onPress={() => console.log('Post Job')}
                        >
                            Đăng tin ngay!
                        </Button>
                    </View>
                </View>

                {/* 4. STATS GRID (Giống "Find Your Job") */}
                <Text variant="titleLarge" style={EmployerHomeStyles.sectionTitle}>Overview</Text>
                <View style={EmployerHomeStyles.gridContainer}>
                    {/* Ô TO BÊN TRÁI (Xanh lơ) */}
                    <TouchableOpacity style={[EmployerHomeStyles.cardLeft, { backgroundColor: '#AFECFE' }]}>
                        <View style={[EmployerHomeStyles.iconCircle, { backgroundColor: 'white' }]}>
                            <MaterialCommunityIcons name="briefcase-search-outline" size={28} color="#0D0D26" />
                        </View>
                        <Text style={EmployerHomeStyles.statNumber}>12</Text>
                        <Text style={EmployerHomeStyles.statLabel}>Active Jobs</Text>
                    </TouchableOpacity>

                    {/* CỘT BÊN PHẢI */}
                    <View style={EmployerHomeStyles.colRight}>
                        {/* Ô nhỏ trên (Tím nhạt) */}
                        <TouchableOpacity style={[EmployerHomeStyles.cardRight, { backgroundColor: '#BEAFFE' }]}>
                            <View style={[EmployerHomeStyles.iconCircle, { backgroundColor: 'white' }]}>
                                <MaterialCommunityIcons name="book-account-outline" size={28} color="#0D0D26" />
                            </View>
                            <Text style={EmployerHomeStyles.statNumberSmall}>45</Text>
                            <Text style={EmployerHomeStyles.statLabel}>New CVs</Text>
                        </TouchableOpacity>
                    </View>
                </View>

                {/* 5. RECENT APPLICANTS LIST (Style thẻ bài giống hình mẫu) */}
                <Text variant="titleLarge" style={EmployerHomeStyles.sectionTitle}>Recent Applicants</Text>

                {recentApplicants.map((item) => (
                    <ApplicantCard
                        key={item.id}
                        item={item}
                        onReviewPress={() => console.log('Xem chi tiết CV', item.id)}
                    />
                ))}

            </ScrollView>
            <FAB
                icon="plus"
                color="white" // Màu icon trắng
                style={EmployerHomeStyles.fab}
                onPress={() => console.log('Đăng tin nhanh')}
                extended={false} // (Tùy chọn) Set true nếu muốn nút dài ra
            />
        </View>
    );
};

export default EmployerHome;