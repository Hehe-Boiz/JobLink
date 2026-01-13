import React, {useMemo, useState, useCallback, useRef, useEffect} from "react";
import {
    View,
    StyleSheet,
    FlatList,
    TouchableOpacity,
    Modal,
    Pressable,
    Animated,
    Dimensions,
    PanResponder, Image,
    TouchableWithoutFeedback
} from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import {MaterialCommunityIcons} from "@expo/vector-icons";
import CustomText from "../../components/common/CustomText";
import JobCard from "../../components/Candidate/JobCard";

const {height: screenHeight} = Dimensions.get("window");
const CLOSE_THRESHOLD = 120;

const MOCK_SAVED = [
    {
        id: "1",
        title: "UI/UX Designer",
        company: "Google inc",
        location: "California, USA",
        logo: "https://img.icons8.com/color/480/google-logo.png",
        tags: ["Design", "Full time", "Senior designer"],
        salary: "$15K",
        period: "Mo",
        posted: "25 minute ago",
        saved: true,
    },
    {
        id: "2",
        title: "Lead Designer",
        company: "Dribbble inc",
        location: "California, USA",
        logo: "https://img.icons8.com/fluency/480/dribbble.png",
        tags: ["Design", "Full time", "Senior designer"],
        salary: "$20K",
        period: "Mo",
        posted: "25 minute ago",
        saved: true,
    },
    {
        id: "3",
        title: "UX Researcher",
        company: "Twitter inc",
        location: "California, USA",
        logo: "https://img.icons8.com/color/480/twitter--v1.png",
        tags: ["Design", "Full time", "Senior designer"],
        salary: "$12K",
        period: "Mo",
        posted: "25 minute ago",
        saved: true,
    },
];

const SavedJobsScreen = ({navigation}) => {
    const [savedJobs, setSavedJobs] = useState(MOCK_SAVED);

    const [sheetVisible, setSheetVisible] = useState(false);
    const [selectedJob, setSelectedJob] = useState(null);

    const translateY = useRef(new Animated.Value(screenHeight)).current;

    const openSheet = useCallback((job) => {
        setSelectedJob(job);
        setSheetVisible(true);

        translateY.setValue(screenHeight);
        Animated.timing(translateY, {
            toValue: 0,
            duration: 300,
            useNativeDriver: true,
        }).start();
    }, [translateY]);

    const closeSheet = useCallback(() => {
        Animated.timing(translateY, {
            toValue: screenHeight,
            duration: 200,
            useNativeDriver: true,
        }).start(({finished}) => {
            if (finished) {
                setSheetVisible(false);
                setSelectedJob(null);
                translateY.setValue(screenHeight);
            }
        });
    }, [translateY]);

    const panResponder = useRef(
        PanResponder.create({
            onStartShouldSetPanResponder: () => true, // QUAN TRỌNG
            onMoveShouldSetPanResponder: (_, gesture) => {
                return Math.abs(gesture.dy) > Math.abs(gesture.dx); // giống CustomSelector
            },
            onPanResponderMove: (_, gesture) => {
                if (gesture.dy > 0) translateY.setValue(gesture.dy);
            },
            onPanResponderRelease: (_, gesture) => {
                if (gesture.dy > CLOSE_THRESHOLD) {
                    closeSheet();
                } else {
                    Animated.spring(translateY, {
                        toValue: 0,
                        useNativeDriver: true,
                        tension: 100,
                        friction: 10,
                    }).start();
                }
            },
        })
    ).current;

    const handleToggleSave = useCallback((jobId) => {
        setSavedJobs((prev) => prev.filter((j) => j.id !== jobId));
    }, []);

    const handleDeleteAll = useCallback(() => {
        setSavedJobs([]);
    }, []);

    const handleApply = useCallback((jobId) => {
        closeSheet();
    }, [closeSheet]);

    const handleDeleteOne = useCallback(() => {
        if (!selectedJob) return;
        setSavedJobs((prev) => prev.filter((j) => j.id !== selectedJob.id));
        closeSheet();
    }, [selectedJob, closeSheet]);

    const renderItem = useCallback(({item}) => {
        return (
            <View style={{marginBottom: 6}}>
                <JobCard
                    item={item}
                    variant="search"
                    onSavePress={handleToggleSave}
                    onApplyPress={handleApply}
                    showMore
                    onMorePress={(job) => openSheet(job)}
                    action="more"
                />
            </View>
        );
    }, [handleApply, handleToggleSave, openSheet]);

    const keyExtractor = useCallback((item) => item.id, []);

    const hasSavings = useMemo(() => savedJobs.length > 0, [savedJobs.length]);

    return (
        <SafeAreaView style={styles.safe}>
            <View style={styles.container}>
                {/* Header */}
                <View style={styles.headerRow}>
                    <CustomText style={styles.headerTitle}>Save Job</CustomText>

                    {hasSavings && (
                        <TouchableOpacity onPress={handleDeleteAll} activeOpacity={0.7}>
                            <CustomText style={styles.deleteAll}>Delete all</CustomText>
                        </TouchableOpacity>
                    )}
                </View>

                {/* Body */}
                {hasSavings ? (
                    <FlatList
                        contentContainerStyle={styles.listContent}
                        data={savedJobs}
                        renderItem={renderItem}
                        keyExtractor={keyExtractor}
                        showsVerticalScrollIndicator={false}
                    />
                ) : (
                    <View style={styles.emptyWrap}>
                        <CustomText style={styles.emptyTitle}>No Savings</CustomText>
                        <CustomText style={styles.emptyDesc}>
                            You don't have any jobs saved, please{"\n"}find it in search to save jobs
                        </CustomText>

                        <Image source={require('../../../assets/images/Illustration.png')} style={styles.imgNoFind}/>

                        <TouchableOpacity
                            style={styles.findBtn}
                            activeOpacity={0.85}
                            onPress={() => navigation?.navigate?.("CandidateSearch")}
                        >
                            <CustomText style={styles.findBtnText}>FIND A JOB</CustomText>
                        </TouchableOpacity>
                    </View>
                )}

                {/* Options Bottom Sheet */}
                <Modal
                    transparent
                    visible={sheetVisible}
                    animationType="none"
                    onRequestClose={closeSheet}
                >
                    {/* Lớp ngoài: bấm ngoài sheet để đóng */}
                    <TouchableWithoutFeedback onPress={closeSheet}>
                        <View style={styles.modalOverlay}>
                            {/* Lớp trong: chặn để sheet nhận gesture, không bị overlay ăn */}
                            <TouchableWithoutFeedback>
                                <Animated.View
                                    style={[
                                        styles.sheet,
                                        {transform: [{translateY}]},
                                    ]}
                                >
                                    {/* Handle kéo */}
                                    <View style={styles.handleTouchArea} {...panResponder.panHandlers}>
                                        <View style={styles.sheetHandle}/>
                                    </View>

                                    {/* Items */}
                                    <TouchableOpacity style={styles.sheetItem} activeOpacity={0.7} onPress={closeSheet}>
                                        <MaterialCommunityIcons name="send-outline" size={22} color="#1E1E1E"/>
                                        <CustomText style={styles.sheetText}>Send message</CustomText>
                                    </TouchableOpacity>

                                    <TouchableOpacity style={styles.sheetItem} activeOpacity={0.7} onPress={closeSheet}>
                                        <MaterialCommunityIcons name="share-variant-outline" size={22} color="#1E1E1E"/>
                                        <CustomText style={styles.sheetText}>Shared</CustomText>
                                    </TouchableOpacity>

                                    <TouchableOpacity style={styles.sheetItem} activeOpacity={0.7}
                                                      onPress={handleDeleteOne}>
                                        <MaterialCommunityIcons name="trash-can-outline" size={22} color="#1E1E1E"/>
                                        <CustomText style={styles.sheetText}>Delete</CustomText>
                                    </TouchableOpacity>

                                    <TouchableOpacity
                                        style={styles.applyBtn}
                                        activeOpacity={0.9}
                                        onPress={() => selectedJob && handleApply(selectedJob.id)}
                                    >
                                        <View style={styles.applyLeft}>
                                            <View style={styles.checkCircle}>
                                                <MaterialCommunityIcons name="check" size={16} color="#FFFFFF"/>
                                            </View>
                                            <CustomText style={styles.applyText}>Apply</CustomText>
                                        </View>
                                    </TouchableOpacity>
                                </Animated.View>
                            </TouchableWithoutFeedback>
                        </View>
                    </TouchableWithoutFeedback>
                </Modal>
            </View>
        </SafeAreaView>
    );
};

export default SavedJobsScreen;

const styles = StyleSheet.create({
    safe: {
        flex: 1,
        backgroundColor: "#F2F3F7"
    },
    container: {
        flex: 1,
        paddingHorizontal: 18,
        paddingTop: 8
    },

    headerRow: {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        paddingVertical: 10,
    },
    headerTitle: {
        fontSize: 22,
        fontWeight: "700",
        color: "#1E1E1E"
    },
    deleteAll: {
        fontSize: 14,
        fontWeight: "600",
        color: "#F28B2C"
    },

    listContent: {
        paddingTop: 8,
        paddingBottom: 24
    },

    emptyWrap: {
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        paddingHorizontal: 18,
    },
    emptyTitle: {
        fontSize: 20,
        fontWeight: "700",
        color: "#1E1E1E",
        marginBottom: 8
    },
    emptyDesc: {
        fontSize: 13,
        color: "#6B6F76",
        textAlign: "center",
        lineHeight: 18
    },
    emptyIconBox: {
        marginTop: 18,
        marginBottom: 22
    },
    findBtn: {
        marginTop: 10,
        height: 52,
        borderRadius: 14,
        alignSelf: "stretch",
        backgroundColor: "#120160",
        alignItems: "center",
        justifyContent: "center",
    },
    findBtnText: {
        color: "#FFFFFF",
        fontWeight: "700",
        letterSpacing: 0.6
    },

    backdrop: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: "rgba(0,0,0,0.28)"
    },
    sheet: {
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "#FFFFFF",
        borderTopLeftRadius: 22,
        borderTopRightRadius: 22,
        paddingHorizontal: 18,
        paddingTop: 10,
        paddingBottom: 22,
        zIndex: 10,
        elevation: 10,
    },
    sheetHandle: {
        alignSelf: "center",
        width: 44,
        height: 5,
        borderRadius: 10,
        backgroundColor: "#D9D9DE",
        marginBottom: 14,
        marginTop: 14,
    },
    sheetItem: {
        flexDirection: "row",
        alignItems: "center",
        height: 52,
    },
    sheetText: {
        marginLeft: 12,
        fontSize: 15,
        color: "#1E1E1E",
        fontWeight: "500"
    },

    applyBtn: {
        marginTop: 8,
        height: 52,
        borderRadius: 8,
        backgroundColor: "#130160",
        justifyContent: "center",
        paddingHorizontal: 16,
    },
    applyLeft: {
        flexDirection: "row",
        alignItems: "center"
    },
    checkCircle: {
        width: 24,
        height: 24,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: "rgba(255,255,255,0.35)",
        alignItems: "center",
        justifyContent: "center",
        marginRight: 10,
    },
    applyText: {
        color: "#FFFFFF",
        fontWeight: "700",
        fontSize: 15
    },
    handleTouchArea: {
        alignSelf: "stretch",
        height: 40,
        alignItems: "center",
        justifyContent: "center",
    },
    modalRoot: {
        flex: 1,
        justifyContent: "flex-end",
    },
    imgNoFind: {
        marginTop: 60,
        marginBottom: 60
    },
    modalOverlay: {
        flex: 1,
        backgroundColor: "rgba(0,0,0,0.28)",
        justifyContent: "flex-end",
    },

});
