import React, {useState, useMemo, useContext} from "react";
import {SafeAreaView} from "react-native-safe-area-context";
import {ScrollView, TouchableOpacity, View, StyleSheet, Image, Alert} from "react-native";
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from "../../components/CustomText";
import JobDescriptionTab from "../../components/Job/JobDetail/JobDetailDescription";
import CompanyTab from "../../components/Job/JobDetail/JobDetailCompany";
import styles from '../../styles/Candidate/CandidateJobDetailStyles'
import JobApplicantsTab from "../../components/Job/JobDetail/JobApplicantsTab";
import {MyUserContext} from "../../utils/contexts/MyContext";
import {Portal, Dialog, Button} from 'react-native-paper';
import JobLogo from "../../components/Job/JobLogo";
import CustomHeader from "../../components/CustomHeader"

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
        {title: "Industry", value: "Internet product"},
        {title: "Employee size", value: "132,121 Employees"},
        {title: "Head office", value: "Mountain View, California, Amerika Serikat"},
        {title: "Type", value: "Multinational company"},
        {title: "Since", value: "1998"},
        {title: "Specialization", value: "Search technology, Web computing, Software and Online advertising"}
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
const MOCK_APPLICANTS = [
    {
        id: 1,
        name: 'Nguyễn Văn An',
        email: 'an.nguyen@email.com',
        status: 'Chờ duyệt',
        statusColor: '#FF9228',
        bg: '#FFF4E5',
        avatar: 'https://randomuser.me/api/portraits/men/32.jpg'
    },
    {
        id: 2,
        name: 'Phạm Thị Dung',
        email: 'dung.pham@email.com',
        status: 'Đã xem',
        statusColor: '#2E5CFF',
        bg: '#E6E1FF',
        avatar: 'https://randomuser.me/api/portraits/women/44.jpg'
    },
    {
        id: 3,
        name: 'Lê Hoàng',
        email: 'hoang.le@email.com',
        status: 'Từ chối',
        statusColor: '#FF4D4D',
        bg: '#FFECEC',
        avatar: 'https://randomuser.me/api/portraits/men/45.jpg'
    },
];

const JobDetail = ({navigation, route}) => {
    const [user,] = useContext(MyUserContext)
    const applicants = MOCK_APPLICANTS;
    const item = MOCK_JOB_DETAIL;
    const [activeTab, setActiveTab] = useState(0);
    const [isSaved, setIsSaved] = useState(false);
    const isEmployer = user?.role === "EMPLOYER";
    const toggleSave = () => {
        setIsSaved(!isSaved);
    };
    const handleApply = () => {
        // Alert.alert("Thành công", "Bạn đã ứng tuyển vào vị trí này!");
        showDialog();
    };

    const [visibleDialog, setVisibleDialog] = useState(false);
    const showDialog = () => setVisibleDialog(true);
    const hideDialog = () => setVisibleDialog(false);
    // const isEmployer = user.role == "EMPLOYER" ? true : false;
    return (
        <View style={{flex: 1}}>
            <SafeAreaView style={[styles.container]} edges={['top', 'left', 'right']}>
                <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{paddingBottom: 130}}>
                    <CustomHeader navigation={navigation}/>

                    <View style={styles.section}>
                        <JobLogo item={item}/>

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
                            {isEmployer &&
                                <TouchableOpacity
                                    style={[styles.tabButton, activeTab === 2 && styles.activeTab]}
                                    onPress={() => setActiveTab(2)}
                                >
                                    <CustomText style={[styles.tabText, activeTab === 2 && styles.activeTabText]}>
                                        Applicants
                                    </CustomText>
                                </TouchableOpacity>
                            }
                        </View>

                        {activeTab === 0 && <JobDescriptionTab item={item}/>}
                        {activeTab === 1 && <CompanyTab item={item}/>}
                        {activeTab === 2 && isEmployer && <JobApplicantsTab job={route.params.job}/>}

                    </View>
                </ScrollView>
            </SafeAreaView>
            {!isEmployer && (
                <View style={styles.footer}>
                    <TouchableOpacity style={styles.btnBookmark} onPress={toggleSave}>
                        <MaterialCommunityIcons
                            name={isSaved ? "bookmark" : "bookmark-outline"}
                            size={28}
                            color={isSaved ? "#FF9228" : "#524B6B"}
                        />
                    </TouchableOpacity>

                    {/* Nút Apply Now */}
                    <TouchableOpacity style={styles.btnApply} onPress={handleApply}>
                        <CustomText style={styles.btnApplyText}>APPLY NOW</CustomText>
                    </TouchableOpacity>
                </View>
            )}
            <Portal>
                <Dialog
                    visible={visibleDialog}
                    onDismiss={hideDialog}
                    style={styles.dialogContainer}
                >
                    <View style={styles.dialogContentWrapper}>
                        <Image
                            source={{uri: 'https://cdn-icons-png.flaticon.com/512/148/148767.png'}}
                            style={styles.dialogIcon}
                        />

                        <CustomText style={styles.dialogTitle}>
                            Thành Công!
                        </CustomText>

                        <Dialog.Content>
                            <CustomText style={styles.dialogText}>
                                Hồ sơ của bạn đã được gửi đến nhà tuyển dụng. Chúc bạn may mắn!
                            </CustomText>
                        </Dialog.Content>

                        <Dialog.Actions style={styles.dialogActions}>
                            <Button
                                mode="contained"
                                onPress={hideDialog}
                                style={styles.dialogButton}
                                labelStyle={styles.dialogButtonLabel}
                            >
                                TUYỆT VỜI
                            </Button>
                        </Dialog.Actions>
                    </View>
                </Dialog>
            </Portal>
        </View>
    );
};

export default JobDetail;


