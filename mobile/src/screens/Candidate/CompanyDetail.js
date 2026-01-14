import React, { useState } from 'react';
import { View, ScrollView, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import CustomHeader from '../../components/common/CustomHeader';
import CustomText from '../../components/common/CustomText';
import CustomFooter from '../../components/common/CustomFooter';
import JobLogo from '../../components/Job/JobLogo';
import JobDetailCompany from '../../components/Job/JobDetail/JobDetailCompany';
import CompanyDetailPost from '../../components/Company/CompanyDetailPost';
import CompanyDetailJobs from '../../components/Company/CompanyDetailJobs';
import {SafeAreaView} from "react-native-safe-area-context";
import stylesJD from '../../styles/Job/JobDetailStyles';
import styles from '../../styles/Candidate/CompanyDetail'

const MOCK_COMPANY_INFO = {
    id: '1',
    logo: 'https://cdn-icons-png.flaticon.com/512/2991/2991148.png',
    title: 'UI/UX Designer',
    company: 'Google',
    location: 'California',
    postedTime: '1 day ago',
    website: 'https://www.google.com',
    aboutCompany: "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium...",
    company_info: [
        {title: "Industry", value: "Internet product"},
        {title: "Employee size", value: "132,121 Employees"},
        {title: "Head office", value: "Mountain View, California"},
    ],
    company_gallery: [
        "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=800&q=80",
    ]
};

const CompanyDetail = ({ navigation }) => {
    const [activeTab, setActiveTab] = useState('About us');
    const item = MOCK_COMPANY_INFO;

    const SaveButton = (
         <TouchableOpacity style={stylesJD.btnBookmark}>
            <MaterialCommunityIcons name="bookmark-outline" size={28} color="#FCA34D" />
        </TouchableOpacity>
    );

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: '#F9F9F9' }}>
            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 100 }}>
                <CustomHeader navigation={navigation} />

                <View style={stylesJD.section}>
                    <JobLogo item={item} />

                    <View style={styles.tabContainer}>
                        {['About us', 'Post', 'Jobs'].map((tab) => {
                            const isActive = activeTab === tab;
                            return (
                                <TouchableOpacity
                                    key={tab}
                                    style={[styles.tabButton, isActive && styles.activeTabButton]}
                                    onPress={() => setActiveTab(tab)}
                                >
                                    <CustomText style={[styles.tabText, isActive && styles.activeTabText]}>
                                        {tab}
                                    </CustomText>
                                </TouchableOpacity>
                            );
                        })}
                    </View>

                    <View style={{ marginTop: 10 }}>
                        {activeTab === 'About us' && <JobDetailCompany item={item} />}
                        {activeTab === 'Post' && <CompanyDetailPost item={item} />}
                        {activeTab === 'Jobs' && <CompanyDetailJobs navigation={navigation} />}
                    </View>
                </View>
            </ScrollView>

            {/* 5. Footer (Apply Now) */}
            <CustomFooter
                onApply={() => console.log('Apply Now Clicked')}
                applyTitle="APPLY NOW"
                leftContent={SaveButton}
            />
        </SafeAreaView>
    );
};

export default CompanyDetail;