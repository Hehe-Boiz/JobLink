import React, {useCallback, useEffect, useState} from 'react';
import {
    ActivityIndicator,
    Alert,
    RefreshControl,
    ScrollView,
    TouchableOpacity,
    View,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

import CustomHeader from '../../components/common/CustomHeader';
import CustomText from '../../components/common/CustomText';
import styles from '../../styles/Candidate/ApplicationMatchAnalysisStyles';
import {authApis, endpoints} from '../../utils/Apis';

const getSkillName = (skill) => {
    if (typeof skill === 'string') return skill;

    return skill?.requirement_skill
        || skill?.canonical_skill
        || skill?.requirement_text
        || skill?.candidate_skill?.canonical_skill
        || 'Skill not specified';
};

const formatSkillName = (skill) => String(skill)
    .replace(/[_-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const formatDate = (value) => {
    if (!value) return 'Previous analysis';

    const date = new Date(value);
    return Number.isNaN(date.getTime())
        ? 'Previous analysis'
        : date.toLocaleDateString();
};

const getScoreMeta = (score) => {
    if (score >= 75) {
        return {label: 'Strong match', color: '#168A63', backgroundColor: '#E8F7F0'};
    }

    if (score >= 50) {
        return {label: 'Potential match', color: '#AF5510', backgroundColor: '#FFF4E5'};
    }

    return {label: 'Needs improvement', color: '#C34343', backgroundColor: '#FFF0F0'};
};

const SkillSection = ({title, icon, skills, tone, emptyText}) => (
    <View style={styles.detailSection}>
        <View style={styles.sectionHeader}>
            <View style={[styles.sectionIcon, styles[`sectionIcon${tone}`]]}>
                <MaterialCommunityIcons name={icon} size={18} color={styles[`sectionIconText${tone}`].color}/>
            </View>
            <CustomText style={styles.sectionTitle}>{title}</CustomText>
            <CustomText style={styles.sectionCount}>{skills.length}</CustomText>
        </View>

        {skills.length > 0 ? (
            <View style={styles.skillList}>
                {skills.map((skill, index) => (
                    <View
                        key={skill?.requirement_id || skill?.requirement_skill || index}
                        style={[styles.skillChip, styles[`skillChip${tone}`]]}
                    >
                        <CustomText style={[styles.skillChipText, styles[`skillChipText${tone}`]]}>
                            {formatSkillName(getSkillName(skill))}
                        </CustomText>
                    </View>
                ))}
            </View>
        ) : (
            <CustomText style={styles.emptySectionText}>{emptyText}</CustomText>
        )}
    </View>
);

const ApplicationMatchAnalysis = ({navigation, route}) => {
    const {applicationId, jobTitle} = route.params || {};
    const [analysis, setAnalysis] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [running, setRunning] = useState(false);
    const [loadingDetail, setLoadingDetail] = useState(false);
    const [loadError, setLoadError] = useState('');

    const loadAnalyses = useCallback(async (showLoader = true) => {
        if (!applicationId) {
            setLoadError('Không tìm thấy hồ sơ ứng tuyển để phân tích.');
            setLoading(false);
            return;
        }

        if (showLoader) {
            setLoading(true);
        } else {
            setRefreshing(true);
        }
        setLoadError('');

        try {
            const token = await AsyncStorage.getItem('token');
            const api = authApis(token);
            const [latestResult, historyResult] = await Promise.allSettled([
                api.get(endpoints.candidate_application_match(applicationId)),
                api.get(endpoints.candidate_application_match_history(applicationId)),
            ]);

            if (latestResult.status === 'fulfilled') {
                setAnalysis(latestResult.value.data);
            } else if (latestResult.reason?.response?.status !== 404) {
                setLoadError('Không thể tải kết quả phân tích. Vui lòng thử lại.');
            } else {
                setAnalysis(null);
            }

            if (historyResult.status === 'fulfilled') {
                const analyses = Array.isArray(historyResult.value.data)
                    ? historyResult.value.data
                    : historyResult.value.data.results || [];
                setHistory(analyses);
            }
        } catch (error) {
            console.error('Lỗi tải phân tích CV:', error);
            setLoadError('Không thể tải kết quả phân tích. Vui lòng thử lại.');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, [applicationId]);

    useEffect(() => {
        loadAnalyses();
    }, [loadAnalyses]);

    const runAnalysis = async () => {
        if (!applicationId || running) return;

        setRunning(true);
        try {
            const token = await AsyncStorage.getItem('token');
            const res = await authApis(token).post(endpoints.candidate_application_match(applicationId));
            setAnalysis(res.data);
            setHistory(previous => [res.data, ...previous.filter(item => item.id !== res.data.id)]);
        } catch (error) {
            console.error('Lỗi phân tích CV:', error);
            const message = error.response?.data?.detail || 'Không thể phân tích CV lúc này. Vui lòng thử lại.';
            Alert.alert('Phân tích chưa hoàn tất', message);
        } finally {
            setRunning(false);
        }
    };

    const selectAnalysis = async (analysisId) => {
        if (!analysisId || analysisId === analysis?.id || loadingDetail) return;

        setLoadingDetail(true);
        try {
            const token = await AsyncStorage.getItem('token');
            const res = await authApis(token).get(
                endpoints.candidate_application_match_detail(applicationId, analysisId)
            );
            setAnalysis(res.data);
        } catch (error) {
            console.error('Lỗi tải chi tiết phân tích:', error);
            Alert.alert('Không thể mở phân tích', 'Vui lòng thử lại sau.');
        } finally {
            setLoadingDetail(false);
        }
    };

    const renderEmptyState = () => (
        <View style={styles.emptyCard}>
            <View style={styles.emptyIcon}>
                <MaterialCommunityIcons name="file-search-outline" size={34} color="#FF9228"/>
            </View>
            <CustomText style={styles.emptyTitle}>Check your CV match</CustomText>
            <CustomText style={styles.emptyText}>
                Compare your submitted CV with this job’s requirements to see your strengths and gaps.
            </CustomText>
            <TouchableOpacity style={styles.runButton} onPress={runAnalysis} disabled={running}>
                {running ? (
                    <ActivityIndicator size="small" color="#FFFFFF"/>
                ) : (
                    <MaterialCommunityIcons name="chart-donut-variant" size={20} color="#FFFFFF"/>
                )}
                <CustomText style={styles.runButtonText}>
                    {running ? 'ANALYZING CV...' : 'ANALYZE CV MATCH'}
                </CustomText>
            </TouchableOpacity>
        </View>
    );

    const renderAnalysis = () => {
        if (!analysis) return renderEmptyState();

        if (analysis.status === 'FAILED') {
            return (
                <View style={styles.failedCard}>
                    <MaterialCommunityIcons name="alert-circle-outline" size={30} color="#C34343"/>
                    <CustomText style={styles.failedTitle}>Analysis could not be completed</CustomText>
                    <CustomText style={styles.failedText}>
                        {analysis.error_message || 'Please review your CV and try again.'}
                    </CustomText>
                    <TouchableOpacity style={styles.retryButton} onPress={runAnalysis} disabled={running}>
                        <CustomText style={styles.retryButtonText}>TRY AGAIN</CustomText>
                    </TouchableOpacity>
                </View>
            );
        }

        if (analysis.status !== 'COMPLETED') {
            return (
                <View style={styles.pendingCard}>
                    <ActivityIndicator size="large" color="#FF9228"/>
                    <CustomText style={styles.pendingTitle}>Your CV is being analyzed</CustomText>
                    <CustomText style={styles.pendingText}>Pull down to refresh the latest result.</CustomText>
                </View>
            );
        }

        const score = Number(analysis.final_score) || 0;
        const scoreMeta = getScoreMeta(score);
        const breakdown = analysis.breakdown || {};
        const breakdownItems = [
            {label: 'Required skills', value: breakdown.required_skills?.score},
            {label: 'Preferred skills', value: breakdown.preferred_skills?.score},
            {label: 'CV evidence', value: breakdown.evidence_quality?.score},
        ].filter(item => item.value !== undefined && item.value !== null);

        return (
            <>
                <View style={styles.summaryCard}>
                    <View style={[styles.scoreCircle, {backgroundColor: scoreMeta.backgroundColor}]}> 
                        <CustomText style={[styles.scoreValue, {color: scoreMeta.color}]}>{Math.round(score)}</CustomText>
                        <CustomText style={[styles.scoreSuffix, {color: scoreMeta.color}]}>/100</CustomText>
                    </View>
                    <View style={styles.summaryContent}>
                        <View style={[styles.scoreBadge, {backgroundColor: scoreMeta.backgroundColor}]}> 
                            <CustomText style={[styles.scoreBadgeText, {color: scoreMeta.color}]}>{scoreMeta.label}</CustomText>
                        </View>
                        <CustomText style={styles.summaryTitle}>CV compatibility score</CustomText>
                        <CustomText style={styles.summaryText}>
                            Based on your submitted CV and this job’s listed requirements.
                        </CustomText>
                    </View>
                </View>

                {analysis.explanation ? (
                    <View style={styles.explanationCard}>
                        <View style={styles.explanationHeader}>
                            <MaterialCommunityIcons name="lightbulb-on-outline" size={20} color="#FF9228"/>
                            <CustomText style={styles.explanationTitle}>Match summary</CustomText>
                        </View>
                        <CustomText style={styles.explanationText}>{analysis.explanation}</CustomText>
                    </View>
                ) : null}

                {breakdownItems.length > 0 ? (
                    <View style={styles.breakdownCard}>
                        <CustomText style={styles.cardTitle}>Score breakdown</CustomText>
                        {breakdownItems.map((item) => (
                            <View key={item.label} style={styles.breakdownRow}>
                                <CustomText style={styles.breakdownLabel}>{item.label}</CustomText>
                                <CustomText style={styles.breakdownValue}>{Math.round(Number(item.value))}%</CustomText>
                            </View>
                        ))}
                    </View>
                ) : null}

                <SkillSection
                    title="Matched skills"
                    icon="check-circle-outline"
                    skills={analysis.matched_skills || []}
                    tone="Matched"
                    emptyText="No direct matches were found."
                />
                <SkillSection
                    title="Partially matched"
                    icon="progress-clock"
                    skills={analysis.partial_skills || []}
                    tone="Partial"
                    emptyText="No partial matches were found."
                />
                <SkillSection
                    title="Skills to strengthen"
                    icon="plus-circle-outline"
                    skills={analysis.missing_skills || []}
                    tone="Missing"
                    emptyText="Great — no missing requirements were identified."
                />

                {(analysis.evidence || []).length > 0 ? (
                    <View style={styles.evidenceCard}>
                        <View style={styles.evidenceHeader}>
                            <MaterialCommunityIcons name="text-box-search-outline" size={20} color="#130160"/>
                            <CustomText style={styles.cardTitle}>Evidence from your CV</CustomText>
                        </View>
                        {analysis.evidence.map((evidence, index) => (
                            <View key={evidence.chunk_key || index} style={styles.evidenceItem}>
                                <CustomText style={styles.evidenceSkills}>
                                    {(evidence.skills || []).map(formatSkillName).join(' • ')}
                                </CustomText>
                                <CustomText style={styles.evidenceText} numberOfLines={3}>
                                    {evidence.text}
                                </CustomText>
                            </View>
                        ))}
                    </View>
                ) : null}
            </>
        );
    };

    if (loading) {
        return (
            <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
                <CustomHeader navigation={navigation} showMenu={false}/>
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color="#FF9228"/>
                    <CustomText style={styles.loadingText}>Loading CV match...</CustomText>
                </View>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <CustomHeader navigation={navigation} showMenu={false}/>
            <ScrollView
                showsVerticalScrollIndicator={false}
                contentContainerStyle={styles.content}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => loadAnalyses(false)} tintColor="#FF9228"/>}
            >
                <CustomText style={styles.pageTitle}>CV match analysis</CustomText>
                <CustomText style={styles.pageSubtitle} numberOfLines={2}>
                    {jobTitle || 'Your application'}
                </CustomText>

                {loadError ? (
                    <TouchableOpacity style={styles.errorBanner} onPress={() => loadAnalyses()}>
                        <MaterialCommunityIcons name="refresh" size={18} color="#AF5510"/>
                        <CustomText style={styles.errorText}>{loadError}</CustomText>
                    </TouchableOpacity>
                ) : null}

                {history.length > 1 ? (
                    <View style={styles.historySection}>
                        <CustomText style={styles.historyTitle}>Previous analyses</CustomText>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.historyList}>
                            {history.map((item) => {
                                const isSelected = item.id === analysis?.id;
                                return (
                                    <TouchableOpacity
                                        key={item.id}
                                        style={[styles.historyItem, isSelected && styles.historyItemActive]}
                                        onPress={() => selectAnalysis(item.id)}
                                    >
                                        <CustomText style={[styles.historyItemDate, isSelected && styles.historyItemDateActive]}>
                                            {formatDate(item.created_date)}
                                        </CustomText>
                                        <CustomText style={[styles.historyItemScore, isSelected && styles.historyItemScoreActive]}>
                                            {item.final_score === null || item.final_score === undefined
                                                ? item.status.toLowerCase()
                                                : `${Math.round(Number(item.final_score))}%`}
                                        </CustomText>
                                    </TouchableOpacity>
                                );
                            })}
                        </ScrollView>
                    </View>
                ) : null}

                {loadingDetail ? (
                    <View style={styles.detailLoading}>
                        <ActivityIndicator size="small" color="#FF9228"/>
                    </View>
                ) : renderAnalysis()}
            </ScrollView>
        </SafeAreaView>
    );
};

export default ApplicationMatchAnalysis;
