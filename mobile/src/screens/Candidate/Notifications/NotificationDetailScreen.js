import React from "react";
import {View, StyleSheet, TouchableOpacity, Image, ScrollView} from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import {MaterialCommunityIcons} from "@expo/vector-icons";
import {Text} from "react-native";
import CustomHeader from "../../../components/common/CustomHeader";

const Bullet = ({text}) => (
    <View style={styles.bulletRow}>
        <View style={styles.bulletDot}/>
        <Text style={styles.bulletText}>{text}</Text>
    </View>
);

const NotificationDetailScreen = ({navigation, route}) => {
    const item = route?.params?.item;

    const data = {
        title: "UI/UX Designer",
        companyLine: "Google inc · California, USA",
        shippedOn: "Shipped on February 14, 2022 at 11:30 am",
        updated: "Updated by recruiter 8 hours ago",
        jobDetails: ["Senior designer", "Full time", "1-3 Years work experience"],
        cvName: "Jamet kudasi - CV - UI/UX Designer.PDF",
        cvMeta: "867 Kb · 14 Feb 2022 at 11:30 am",
        logo: item?.logo ?? "https://img.icons8.com/color/480/google-logo.png",
    };

    return (
        <SafeAreaView style={styles.safe} edges={["top"]}>
            <CustomHeader/>
            <Text style={styles.headerTitle}>Your application</Text>


            <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
                <View style={styles.card}>
                    <View style={styles.logoWrap}>
                        <Image source={{uri: data.logo}} style={styles.logo}/>
                    </View>

                    <Text style={styles.jobTitle}>{data.title}</Text>
                    <Text style={styles.companyLine}>{data.companyLine}</Text>

                    <View style={styles.bullets}>
                        <Bullet text={data.shippedOn}/>
                        <Bullet text={data.updated}/>
                    </View>

                    <Text style={styles.sectionTitle}>Job details</Text>
                    <View style={styles.bullets}>
                        {data.jobDetails.map((t) => (
                            <Bullet key={t} text={t}/>
                        ))}
                    </View>

                    <Text style={styles.sectionTitle}>Application details</Text>
                    <Text style={styles.subSectionTitle}>CV/Resume</Text>

                    <View style={styles.fileCard}>
                        <View style={styles.pdfBadge}>
                            <Text style={styles.pdfText}>PDF</Text>
                        </View>

                        <View style={{flex: 1}}>
                            <Text style={styles.fileName} numberOfLines={1}>
                                {data.cvName}
                            </Text>
                            <Text style={styles.fileMeta}>{data.cvMeta}</Text>
                        </View>

                        <MaterialCommunityIcons name="chevron-right" size={22} color="#8C8C8C"/>
                    </View>

                    <TouchableOpacity style={styles.primaryBtn}>
                        <Text style={styles.primaryBtnText}>APPLY FOR MORE JOBS</Text>
                    </TouchableOpacity>
                </View>
            </ScrollView>
        </SafeAreaView>
    );
};

export default NotificationDetailScreen;


const styles = StyleSheet.create({
    safe: {
        flex: 1,
        backgroundColor: "#F9F9F9"
    },
    headerTitle: {
        // flex: 1,
        textAlign: "center",
        fontSize: 18,
        fontWeight: "700",
        color: "#131313"
    },

    content: {
        paddingHorizontal: 14,
        // paddingTop: 10,
        paddingBottom: 24,
        marginTop: 30
    },
    card: {
        backgroundColor: "#FFFFFF",
        borderRadius: 22,
        padding: 16,
        borderWidth: 1,
        borderColor: "#EEF0F6",
    },

    logoWrap: {
        width: 46,
        height: 46,
        borderRadius: 14,
        backgroundColor: "#FFFFFF",
        alignItems: "center",
        justifyContent: "center",
        marginBottom: 10,
    },
    logo: {
        width: 30,
        height: 30,
        resizeMode: "contain"
    },

    jobTitle: {
        fontSize: 16,
        fontWeight: "800",
        color: "#171717"
    },
    companyLine: {
        marginTop: 4,
        fontSize: 12,
        color: "#6A6A6A"
    },

    bullets: {
        marginTop: 10,
        gap: 8
    },

    sectionTitle: {
        marginTop: 16,
        fontSize: 13,
        fontWeight: "800",
        color: "#1C1C1C"
    },
    subSectionTitle: {
        marginTop: 10,
        fontSize: 12,
        fontWeight: "800",
        color: "#1C1C1C"
    },

    bulletRow: {
        flexDirection: "row",
        alignItems: "center",
        gap: 10
    },
    bulletDot: {
        width: 5,
        height: 5,
        borderRadius: 99,
        backgroundColor: "#B0B0B0"
    },
    bulletText: {
        flex: 1,
        fontSize: 12,
        color: "#6B6B6B",
        lineHeight: 17
    },

    fileCard: {
        marginTop: 10,
        borderRadius: 16,
        borderWidth: 1.5,
        borderColor: "#E6E8F0",
        padding: 12,
        flexDirection: "row",
        alignItems: "center",
        gap: 12,
        backgroundColor: 'rgba(63, 19, 228, 0.05)',
        borderStyle: "dashed",
    },
    pdfBadge: {
        width: 44,
        height: 44,
        borderRadius: 14,
        backgroundColor: "#FF464B",
        alignItems: "center",
        justifyContent: "center",
    },
    pdfText: {
        color: "#FFFFFF",
        fontWeight: "900"
    },
    fileName: {
        fontSize: 12,
        fontWeight: "800",
        color: "#1E1E1E"
    },
    fileMeta: {
        marginTop: 4,
        fontSize: 11,
        color: "#8A8A8A"
    },

    primaryBtn: {
        marginTop: 16,
        height: 48,
        borderRadius: 8,
        backgroundColor: "#1C157A",
        alignItems: "center",
        justifyContent: "center",
    },
    primaryBtnText: {
        color: "#FFFFFF",
        fontWeight: "900",
        fontSize: 12,
        letterSpacing: 0.5
    },
});
