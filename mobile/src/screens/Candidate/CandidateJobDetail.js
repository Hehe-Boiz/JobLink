import React, {useState, useMemo} from "react";
import {SafeAreaView} from "react-native-safe-area-context";
import {ScrollView, TouchableOpacity, View, StyleSheet, Image} from "react-native";
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from "../../components/CustomText";
import JobDescriptionTab from "../../components/Candidate/JobDetail/CandidateJobDetailDescription";
import CompanyTab from "../../components/Candidate/JobDetail/CandidateJobDetailCompany";
import styles from '../../styles/Candidate/CandidateJobDetailStyles'

const MOCK_JOB_DETAIL = {
    id: '1',
    logo: 'https://cdn-icons-png.flaticon.com/512/2991/2991148.png',
    title: 'UI/UX Designer',
    company: 'Google',
    location: 'California',
    postedTime: '1 day ago',
    desc: "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.",
    requirements: "Sed ut perspiciatis unde omnis iste natus error sit.\nNeque porro quisquam est, qui dolorem ipsum quia dolor sit amet.\nNemo enim ipsam voluptatem quia voluptas sit aspernatur.\nUt enim ad minima veniam, quis nostrum exercitationem.",
    street: "Overlook Avenue, Belleville, NJ, USA",
    link_gg_map: "https://www.google.com/maps/search/?api=1&query=Googleplex+Mountain+View",
    info: [
        {title: "Position", value: "Senior Designer"},
        {title: "Qualification", value: "Bachelor's Degree"},
        {title: "Experience", value: "3 Years"},
        {title: "Job Type", value: "Full-Time"},
        {title: "Specialization", value: "Design"}
    ],
    facilities: "Medical, Dental, Technical Certification, Meal Allowance, Transport Allowance, Monday-Friday",
    aboutCompany: "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.\nAt vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas .\nNor again is there anyone who loves or pursues or desires to obtain pain of itself, because it is pain.",
    company_info: [
        {  title: "Industry", value: "Internet product" },
        {  title: "Employee size", value: "132,121 Employees" },
        {  title: "Head office", value: "Mountain View, California, Amerika Serikat" },
        {  title: "Type", value: "Multinational company" },
        {  title: "Since", value: "1998" },
        {  title: "Specialization", value: "Search technology, Web computing, Software and Online advertising" }
    ],
    company_gallery: [
        "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=800&q=80", 
        "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1568992687947-868a62a9f521?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=800&q=80"
    ]
};

const CandidateJobDetail = ({navigation}) => {
    const item = MOCK_JOB_DETAIL;
    const [activeTab, setActiveTab] = useState(0);


    return (
        <SafeAreaView style={styles.container}>
            <ScrollView showsVerticalScrollIndicator={false}>
                {/* 1. Header Navigation */}
                <View style={styles.headerNav}>
                    <TouchableOpacity onPress={() => navigation?.goBack()}>
                        <MaterialCommunityIcons name="arrow-left" size={24} color="#1A1D1F"/>
                    </TouchableOpacity>
                    <TouchableOpacity>
                        <MaterialCommunityIcons name="dots-horizontal" size={24} color="#1A1D1F"/>
                    </TouchableOpacity>
                </View>

                <View style={styles.section}>
                    <View style={styles.contentLogoContainer}>
                        <View style={styles.logoWrapper}>
                            <Image source={{uri: item.logo}} style={styles.logo}/>
                        </View>
                        <CustomText style={styles.jobTitle}>{item.title}</CustomText>
                        <View style={styles.infoRow}>
                            <CustomText style={styles.infoText}>{item.company}</CustomText>
                            <View style={styles.dot}></View>
                            <CustomText style={styles.infoText}>{item.location}</CustomText>
                            <View style={styles.dot}></View>
                            <CustomText style={styles.infoText}>{item.postedTime}</CustomText>
                        </View>
                    </View>

                    <View style={styles.tabContainer}>
                        <TouchableOpacity
                            style={[styles.tabButton, activeTab === 0 && styles.activeTab]}
                            onPress={() => setActiveTab(0)}
                        >
                            <CustomText style={[styles.tabText, activeTab === 0 && styles.activeTabText]}>
                                Description
                            </CustomText>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[styles.tabButton, activeTab === 1 && styles.activeTab]}
                            onPress={() => setActiveTab(1)}
                        >
                            <CustomText style={[styles.tabText, activeTab === 1 && styles.activeTabText]}>
                                Company
                            </CustomText>
                        </TouchableOpacity>
                    </View>

                    {activeTab === 0 ? (
                        <JobDescriptionTab item={item}/>
                    ) : (
                        <CompanyTab item={item}/>
                    )}

                </View>
            </ScrollView>
        </SafeAreaView>
    );
};

export default CandidateJobDetail;


