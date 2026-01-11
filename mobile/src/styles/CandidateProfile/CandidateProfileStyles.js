import { StyleSheet} from 'react-native';

export default StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F9F9F9',
    },

    headerContainer: {
        height: 250,
        width: '100%',
        borderBottomLeftRadius: 45,
        borderBottomRightRadius: 45,
        overflow: 'hidden',
        position: 'relative',
    },
    bg: {
        position: 'absolute',
        top: -65,
        left: 0,
        right: 0,
        bottom: 0,
    },
    topBar: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    topIcons: {
        flexDirection: 'row',
        gap: 8,
    },
    iconButton: {
        width: 44,
        height: 44,
        justifyContent: 'center',
        alignItems: 'center',
    },
    profileContent: {
        paddingHorizontal: 10,
    },
    avatar: {
        width: 55,
        height: 55,
        borderRadius: 35,
        borderWidth: 2,
        borderColor: 'rgba(255,255,255,0.4)',
        marginBottom: 15,
        marginLeft: 10
    },
    name: {
        fontSize: 16,
        fontWeight: '700',
        color: '#FFF',
        marginBottom: 4,
        marginLeft: 10
    },
    location: {
        fontSize: 13,
        color: 'rgba(255,255,255,0.7)',
        fontWeight: '400',
        marginLeft: 10
    },
    statsRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 25,
        marginHorizontal: 10
    },
    statsGroup: {
        flexDirection: 'row',
        alignItems: 'baseline',
        marginRight: 20,
    },
    statNumber: {
        fontSize: 18,
        fontWeight: '700',
        color: '#FFF',
    },
    statLabel: {
        fontSize: 14,
        color: 'rgba(255,255,255,0.7)',
        fontWeight: '400',
    },
    editButton: {
        flexDirection: 'row',
        backgroundColor: 'rgba(255,255,255,0.13)',
        paddingVertical: 12,
        paddingHorizontal: 17,
        borderRadius: 6,
        alignItems: 'center',
        marginLeft: 'auto',
    },
    editButtonText: {
        color: '#FFF',
        fontSize: 14,
        marginRight: 8,
        fontWeight: '500',
    },

    listContainer: {
        paddingHorizontal: 20,
        paddingTop: 25,
    },

    card: {
        backgroundColor: '#FFF',
        borderRadius: 20,
        padding: 20,
        marginBottom: 15,
        shadowColor: '#130160',
        shadowOffset: {width: 0, height: 4},
        shadowOpacity: 0.06,
        shadowRadius: 10,
        elevation: 3,
    },

    sectionHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    sectionHeaderLeft: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    sectionIconContainer: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: 'rgba(255, 146, 40, 0.12)',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    sectionTitle: {
        fontSize: 15,
        fontWeight: '600',
        color: '#150B3D',
    },
    sectionHeaderBtn: {
        width: 36,
        height: 36,
        borderRadius: 18,
        backgroundColor: 'rgba(255, 146, 40, 0.12)',
        justifyContent: 'center',
        alignItems: 'center',
    },

    aboutText: {
        fontSize: 13,
        color: '#524B6B',
        lineHeight: 20,
        marginTop: 15,
    },

    experienceItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginTop: 18,
        paddingTop: 15,
        borderTopWidth: 1,
        borderTopColor: '#F1F1F5',
    },
    experienceContent: {
        flex: 1,
        marginRight: 15,
    },
    experienceTitle: {
        fontSize: 14,
        fontWeight: '600',
        color: '#150B3D',
        marginBottom: 4,
    },
    experienceCompany: {
        fontSize: 13,
        color: '#524B6B',
        marginBottom: 4,
    },
    experienceDate: {
        fontSize: 12,
        color: '#AAA6B9',
    },

    // Tags (skills, languages)
    tagsContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        marginTop: 15,
        gap: 10,
    },
    tag: {
        backgroundColor: '#F3F2F8',
        paddingHorizontal: 16,
        paddingVertical: 10,
        borderRadius: 8,
    },
    tagText: {
        fontSize: 13,
        color: '#150B3D',
        fontWeight: '500',
    },
    tagMore: {
        backgroundColor: 'transparent',
    },
    tagTextMore: {
        fontSize: 13,
        color: '#AAA6B9',
    },
    seeMoreBtn: {
        marginTop: 15,
        alignSelf: 'center',
    },
    seeMoreText: {
        fontSize: 13,
        color: '#FF9228',
        fontWeight: '500',
    },

    resumeItem: {
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 15,
        paddingTop: 15,
        borderTopWidth: 1,
        borderTopColor: '#F1F1F5',
    },
    resumeIconContainer: {
        width: 44,
        height: 44,
        borderRadius: 10,
        backgroundColor: '#FFF5F5',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    resumeContent: {
        flex: 1,
    },
    resumeName: {
        fontSize: 13,
        fontWeight: '600',
        color: '#150B3D',
        marginBottom: 3,
    },
    resumeInfo: {
        fontSize: 11,
        color: '#AAA6B9',
    },
    deleteBtn: {
        padding: 8,
    },
});