import React, {useMemo, useState, useCallback, useRef, useEffect, useContext} from "react";
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
    TouchableWithoutFeedback,
    Alert
} from "react-native";
import {SafeAreaView} from "react-native-safe-area-context";
import {MaterialCommunityIcons} from "@expo/vector-icons";
import CustomText from "../../components/common/CustomText";
import JobCard from "../../components/Candidate/JobCard";
import Apis, {endpoints, authApis} from '../../utils/Apis';
import {MyUserContext} from '../../utils/contexts/MyContext';
import {useFocusEffect} from "@react-navigation/native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import {formatTimeElapsed} from "../../utils/Helper";

const {height: screenHeight} = Dimensions.get("window");
const CLOSE_THRESHOLD = 120;

const SavedJobsScreen = ({navigation}) => {
    const [user, dispatch] = useContext(MyUserContext);
    const accessToken = user?.token;
    const [savedJobs, setSavedJobs] = useState([]);
    const [sheetVisible, setSheetVisible] = useState(false);
    const [selectedJob, setSelectedJob] = useState(null);
    const translateY = useRef(new Animated.Value(screenHeight)).current;
    const [loading, setLoading] = useState(false);

    const [isCompareMode, setIsCompareMode] = useState(false);
    const [selectedCompareList, setSelectedCompareList] = useState([]);

    const handleToggleSelect = useCallback((job) => {
        const exists = selectedCompareList.find(j => j.id === job.id);

        if (exists) {
            setSelectedCompareList(prev => prev.filter(j => j.id !== job.id));
        } else {
            if (selectedCompareList.length < 5) {
                setSelectedCompareList(prev => [...prev, job]);
            } else {
                Alert.alert("Giới hạn", "Bạn chỉ có thể so sánh tối đa 5 công việc cùng lúc.");
            }
        }
    }, [selectedCompareList]);

    const toggleCompareMode = () => {
        if (isCompareMode) {
            setIsCompareMode(false);
            setSelectedCompareList([]);
        } else {
            setIsCompareMode(true);
        }
    };

    const goToComparison = () => {
        if (selectedCompareList.length < 2) {
            Alert.alert("Thông báo", "Vui lòng chọn ít nhất 2 công việc để so sánh.");
            return;
        }
        navigation.navigate("JobComparison", {selectedJobs: selectedCompareList});
    };

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
            onStartShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponder: (_, gesture) => {
                return Math.abs(gesture.dy) > Math.abs(gesture.dx);
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

    useFocusEffect(
        useCallback(() => {
            loadSavedJobs();
        }, [])
    );

    const loadSavedJobs = async () => {

        try {
            setLoading(true);
            const token = await AsyncStorage.getItem('token');
            const res = await authApis(token).get(endpoints['bookmarks']);

            let dataList = [];
            if (Array.isArray(res.data)) {
                dataList = res.data;
            } else if (res.data && Array.isArray(res.data.results)) {
                dataList = res.data.results;
            }
            console.log("Số lượng job đã lưu:", dataList.length);

            const formattedData = res.data.map(item => {
                const job = item.job;

                const minSalary = job.salary_min ? (job.salary_min / 1000000).toFixed(0) + 'M' : '';
                const maxSalary = job.salary_max ? (job.salary_max / 1000000).toFixed(0) + 'M' : '';
                const salaryString = (minSalary && maxSalary)
                    ? `${minSalary} - ${maxSalary}`
                    : (minSalary || maxSalary || 'Thỏa thuận');

                return {
                    bookmarkId: item.id,
                    id: job.id,
                    title: job.title,
                    company: job.company_name,
                    logo: job.employer_logo || 'https://via.placeholder.com/60',
                    location: job.location?.name || 'Việt Nam',
                    salary: salaryString,
                    period: 'Tháng',
                    tags: [
                        job.category?.name,
                        job.employment_type?.replace('_', ' '),
                        ...(job.tags || []).map(t => t.name || t)
                    ].filter(Boolean),
                    saved: true,
                    posted: formatTimeElapsed(job.updated_date)
                };
            });

            setSavedJobs(formattedData);
        } catch (error) {
            console.error("Lỗi khi tải jobs đã lưu:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleSave = useCallback(async (jobId) => {
        const jobIndex = savedJobs.findIndex(j => j.id === jobId);
        if (jobIndex === -1) return;

        const bookmarkIdToDelete = savedJobs[jobIndex].bookmarkId;

        setSavedJobs((prev) => prev.filter((j) => j.id !== jobId));

        try {
            const token = await AsyncStorage.getItem('token');
            await authApis(token).delete(`${endpoints.bookmarks}${bookmarkIdToDelete}/`);
        } catch (error) {
            console.error("Lỗi khi xóa bookmark:", error);
            Alert.alert("Lỗi", "Không thể bỏ lưu công việc này. Vui lòng thử lại.");
            loadSavedJobs();
        }
    }, [savedJobs, accessToken]);

    const handleDeleteAll = useCallback(() => {
        Alert.alert(
            "Xóa tất cả",
            "Bạn có chắc chắn muốn xóa toàn bộ công việc đã lưu không?",
            [
                {
                    text: "Hủy",
                    style: "cancel"
                },
                {
                    text: "Xóa hết",
                    style: "destructive",
                    onPress: async () => {
                        try {
                            setLoading(true);

                            const token = await AsyncStorage.getItem('token');
                            await authApis(token).delete(`${endpoints['bookmarks']}delete-all/`);
                            setSavedJobs([]);


                        } catch (error) {
                            console.error("Lỗi xóa tất cả:", error);
                            Alert.alert("Lỗi", "Không thể xóa vào lúc này. Vui lòng thử lại sau.");
                        } finally {
                            setLoading(false);
                        }
                    }
                }
            ]
        );
    }, []);

    const handleApply = useCallback((jobId) => {
        closeSheet();
        navigation.navigate("JobDetail", {jobId: jobId});
    }, [closeSheet, navigation]);

    const handleDeleteOne = useCallback(() => {
        if (!selectedJob) return;
        handleToggleSave(selectedJob.id);
        closeSheet();
    }, [selectedJob, closeSheet, handleToggleSave]);

    const renderItem = useCallback(({item}) => {
        const isSelected = selectedCompareList.find(j => j.id === item.id);

        return (
            <View style={{marginBottom: 6}}>
                {isCompareMode && (
                    <TouchableOpacity
                        style={styles.selectionOverlay}
                        onPress={() => handleToggleSelect(item)}
                        activeOpacity={0.8}
                    >
                        <View style={[styles.checkBox, isSelected && styles.checkBoxSelected]}>
                            {isSelected && <MaterialCommunityIcons name="check" size={16} color="#FFF"/>}
                        </View>
                    </TouchableOpacity>
                )}
                <JobCard
                    item={item}
                    variant="search"
                    onSavePress={() => handleToggleSave(item.id)}
                    onApplyPress={() => handleApply(item.id)}
                    showMore={!isCompareMode}
                    onMorePress={(job) => openSheet(job)}
                    action="more"
                    onPress={() => {
                        if (isCompareMode) {
                            handleToggleSelect(item);
                        } else {
                            navigation.navigate("JobDetail", {jobId: item.id});
                        }
                    }}
                />
            </View>
        );
    }, [handleApply, handleToggleSave, openSheet, navigation, isCompareMode, selectedCompareList, handleToggleSelect]);

    const keyExtractor = useCallback((item) => item.id.toString(), []);

    const hasSavings = useMemo(() => savedJobs.length > 0, [savedJobs.length]);

    return (
        <SafeAreaView style={styles.safe}>
            <View style={styles.container}>
                <View style={styles.headerRow}>
                    <CustomText style={styles.headerTitle}>Save Job</CustomText>
                    {hasSavings && (
                        <TouchableOpacity onPress={toggleCompareMode} style={{marginRight: 15}}>
                            <CustomText style={styles.compareText}>
                                {isCompareMode ? "Hủy" : "So sánh"}
                            </CustomText>
                        </TouchableOpacity>
                    )}

                    {hasSavings && !isCompareMode && (
                        <TouchableOpacity onPress={handleDeleteAll} activeOpacity={0.7}>
                            <CustomText style={styles.deleteAll}>Delete All</CustomText>
                        </TouchableOpacity>
                    )}
                </View>

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
                            onPress={() => navigation?.navigate?.("CandidateSearchJob")}
                        >
                            <CustomText style={styles.findBtnText}>FIND A JOB</CustomText>
                        </TouchableOpacity>
                    </View>
                )}

                {isCompareMode && (
                    <View style={styles.floatingBar}>
                        <View>
                            <CustomText style={styles.floatingTitle}>Đã chọn {selectedCompareList.length}/5</CustomText>
                            <CustomText style={styles.floatingSub}>Chọn ít nhất 2 công việc</CustomText>
                        </View>
                        <TouchableOpacity
                            style={[
                                styles.compareButton,
                                selectedCompareList.length < 2 && styles.compareButtonDisabled
                            ]}
                            onPress={goToComparison}
                            disabled={selectedCompareList.length < 2}
                        >
                            <CustomText style={styles.compareButtonText}>So sánh ngay</CustomText>
                            <MaterialCommunityIcons name="arrow-right" size={18} color="#FFF"/>
                        </TouchableOpacity>
                    </View>
                )}

                <Modal
                    transparent
                    visible={sheetVisible}
                    animationType="none"
                    onRequestClose={closeSheet}
                >
                    <TouchableWithoutFeedback onPress={closeSheet}>
                        <View style={styles.modalOverlay}>
                            <TouchableWithoutFeedback>
                                <Animated.View
                                    style={[
                                        styles.sheet,
                                        {transform: [{translateY}]},
                                    ]}
                                >
                                    <View style={styles.handleTouchArea} {...panResponder.panHandlers}>
                                        <View style={styles.sheetHandle}/>
                                    </View>

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
        fontSize: 16,
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
    selectionOverlay: {
        position: 'absolute',
        top: 10,
        right: 10,
        zIndex: 10,
        padding: 5
    },
    checkBox: {
        width: 24,
        height: 24,
        borderRadius: 6,
        borderWidth: 2,
        borderColor: '#130160',
        backgroundColor: '#FFF',
        alignItems: 'center',
        justifyContent: 'center'
    },
    checkBoxSelected: {
        backgroundColor: '#130160',
    },

    floatingBar: {
        position: 'absolute',
        bottom: 20,
        left: 20,
        right: 20,
        backgroundColor: '#FFFFFF',
        borderRadius: 16,
        padding: 16,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        shadowColor: "#000",
        shadowOffset: {width: 0, height: 4},
        shadowOpacity: 0.15,
        shadowRadius: 12,
        elevation: 10,
    },
    floatingTitle: {
        fontSize: 16,
        fontWeight: '700',
        color: '#130160'
    },
    floatingSub: {
        fontSize: 12,
        color: '#6B6F76'
    },
    compareButton: {
        backgroundColor: '#130160',
        paddingVertical: 10,
        paddingHorizontal: 16,
        borderRadius: 10,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6
    },
    compareButtonDisabled: {
        backgroundColor: '#A0A0A0',
    },
    compareButtonText: {
        color: '#FFFFFF',
        fontWeight: '700',
        fontSize: 14
    },
    compareText: {
        fontSize: 16,
        fontWeight: "700",
        color: "#130160"
    }
});
