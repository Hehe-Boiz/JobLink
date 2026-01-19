import { StyleSheet } from 'react-native';

export const COLORS = {
    primary: '#130160',
    secondary: '#524B6B',
    background: '#F5F7FA',
    white: '#FFFFFF',
    border: '#EAEAEA',
    success: '#00C566',
    warning: '#FF9228',
    error: '#FF4D4D',
    info: '#2E5CFF',
    placeholder: '#95969D'
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: COLORS.background,
    },
    // --- Header thông tin Job ---
    jobHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 20,
        backgroundColor: COLORS.white,
        marginHorizontal: 20,
        marginTop: 10,
        marginBottom: 15,
        borderRadius: 20,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 8,
        elevation: 2,
    },
    jobIconBox: {
        width: 54,
        height: 54,
        borderRadius: 18,
        backgroundColor: '#F0F2F5',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 15,
    },
    jobTitle: {
        fontSize: 17,
        fontWeight: '700',
        color: COLORS.primary,
        marginBottom: 6,
    },
    jobSub: {
        fontSize: 14,
        color: COLORS.secondary,
    },
    
    // --- Search Box ---
    searchContainer: {
        paddingHorizontal: 20,
        marginBottom: 15,
    },
    searchBoxModern: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: COLORS.white,
        borderRadius: 30,
        paddingHorizontal: 15,
        height: 56,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.08,
        shadowRadius: 12,
        elevation: 4,
    },
    searchInputModern: {
        flex: 1,
        marginLeft: 12,
        fontSize: 16,
        color: COLORS.primary,
        fontWeight: '500',
        height: '100%',
    },

    // --- List & States ---
    listContent: {
        padding: 20,
        paddingTop: 5,
        paddingBottom: 50
    },
    centerBox: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        marginTop: 50,
    },
    emptyState: {
        alignItems: 'center',
        marginTop: 80,
        opacity: 0.8
    },

    // --- Applicant Card Item ---
    card: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 16,
        marginBottom: 16,
        backgroundColor: COLORS.white,
        borderRadius: 20,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.06,
        shadowRadius: 6,
        elevation: 3,
    },
    avatar: {
        width: 60,
        height: 60,
        borderRadius: 30,
        marginRight: 16,
        backgroundColor: '#F0F0F0',
        borderWidth: 2,
        borderColor: '#FFFFFF',
    },
    content: {
        flex: 1,
        marginRight: 10,
    },
    rowBetween: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
    },
    name: {
        fontSize: 16,
        fontWeight: '700',
        color: COLORS.primary,
        flex: 1,
        marginRight: 8,
    },
    badge: {
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 20,
    },
    badgeText: {
        fontSize: 12,
        fontWeight: '700',
    },
    infoRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 6,
    },
    email: {
        fontSize: 14,
        color: COLORS.secondary,
        marginLeft: 8,
    },
    date: {
        fontSize: 13,
        color: '#AAA6B9',
        marginLeft: 8,
    },
});

export default styles;